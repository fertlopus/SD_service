from fastapi import FastAPI, status, Depends, HTTPException
from service.db_settings.settings import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from service.models import schemas
from service.db_settings.database import create_async_engine, create_all_tables, get_async_session
from service.db_settings.models import GeneratedImage
from service.storage_utils.storage import Storage
from utils.worker import text_to_image_task
import contextlib


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield


app = FastAPI()


async def get_generated_image_or_404(id: int,
                                     session: AsyncSession = Depends(get_async_session)) -> GeneratedImage:
    """
    Asynchronously retrieves a generated image by its ID or raises an HTTP 404 error if not found.
    This function executes an asynchronous query to fetch an instance of GeneratedImage from a database.
    If the image with the specified ID does not exist, it raises an HTTP 404 exception.

    Args:
        id (int): The unique identifier of the generated image to retrieve.
        session (AsyncSession, optional): The database session dependency. If not provided, it is obtained via
                                              the get_async_session dependency.

    Returns:
        GeneratedImage: The retrieved image object associated with the given ID.

    Raises:
        HTTPException: An error with status code 404 if no image with the specified ID is found in the database.

    Usage example:
        # Asynchronously get an image with ID of 1
        image = await get_generated_image_or_404(id=1)
    """
    select_query = select(GeneratedImage).where(GeneratedImage.id == id)
    result = await session.execute(select_query)
    image = result.scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return image


async def get_storage() -> Storage:
    return Storage()


@app.post("/generated-images", response_model=schemas.GeneratedImageRead, status_code=status.HTTP_201_CREATED)
async def create_generated_image(generated_image_create: schemas.GeneratedImageCreate,
                                 session: AsyncSession = Depends(get_async_session)) -> GeneratedImage:
    """
    Asynchronously creates a new generated image record in the database and triggers an image generation task.

    This endpoint handles POST requests to create a new GeneratedImage record. It accepts the image creation
    details as a request model, saves the new record, commits the transaction, and sends a task for
    image generation. The response model ensures that only specified fields are returned to the client.

    Args:
        generated_image_create (schemas.GeneratedImageCreate): The schema representing the fields required
                                                              to create a new GeneratedImage record.
        session (AsyncSession, optional): The database session dependency. If not provided, it is obtained
                                          via the get_async_session dependency.

    Returns:
        GeneratedImage: The newly created GeneratedImage record.

    Raises:
        HTTPException: Any exception thrown during the process would result in an HTTP error response.

    Usage example:
        # Create a new generated image record via POST request
        new_image_record = await create_generated_image(generated_image_create_model)
    """
    image = GeneratedImage(**generated_image_create.model_dump())
    session.add(image)
    await session.commit()
    text_to_image_task.send(image.id)
    return image


@app.get("/generated-images/{id}", response_model=schemas.GeneratedImageRead)
async def get_generated_image(image: GeneratedImage = Depends(get_generated_image_or_404)) -> GeneratedImage:
    return image


@app.get("/generated-images/{id}/url")
async def get_generated_image_url(image: GeneratedImage = Depends(get_generated_image_or_404),
                                  storage: Storage = Depends(get_storage)) -> schemas.GeneratedImageURL:
    if image.file_name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image is not available yet. Please try again later.",
        )

    url = storage.get_presigned_url(image.file_name, settings.storage_bucket)
    return schemas.GeneratedImageURL(url=url)
