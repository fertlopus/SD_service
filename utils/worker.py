import uuid
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware.middleware import Middleware
from sqlalchemy import select
from service.db_settings.database import async_session_maker
from service.db_settings.models import GeneratedImage
from service.db_settings.settings import settings
from service.storage_utils.storage import Storage
from service.text_to_image import TextToImage
import asyncio


class TextToImageMiddleware(Middleware):
    """
    Middleware class for integrating Text to Image conversion functionality into a processing pipeline.

    This middleware leverages the TextToImage class to load and provide a Stable Diffusion model
    that can convert text descriptions into images during the post-boot process of a broker system.
    More about the parent class -> https://dramatiq.io/reference.html#middleware

    Attributes:
        text_to_image (TextToImage): An instance of TextToImage for text to image conversion.

    Methods:
        __init__():
            Initializes a new instance of TextToImageMiddleware, setting up the underlying TextToImage instance.

        after_process_boot(broker):
            Called after the processing system boots up, this method loads the text-to-image model.

            Args:
                broker: The broker system that the middleware is part of.

            Returns:
                The result of the parent class's after_process_boot method, typically None.
    """

    def __init__(self) -> None:
        super().__init__()
        self.text_to_image = TextToImage()

    def after_process_boot(self, broker):
        """
        Load the text-to-image model after the broker system boots up.

        Args:
            broker: The broker system that the middleware is part of.

        Returns:
            The result of the parent class's after_process_boot method.
        """
        self.text_to_image.load_model()
        return super().after_process_boot(broker)


text_to_image_middleware = TextToImageMiddleware()
redis_broker = RedisBroker(host = "localhost")
redis_broker.add_middleware(text_to_image_middleware)
dramatiq.set_broker(redis_broker)


# The worker configuration
# To run the service worker open terminal and type: $ dramatiq -p 1 -t 1 utils.worker
# -p is the number of processes and -t is the number of threads
def get_image(id: int) -> GeneratedImage:
    async def _get_image(id: int) -> GeneratedImage:
        async with async_session_maker() as session:
            select_query = select(GeneratedImage).where(GeneratedImage.id == id)
            result = await session.execute(select_query)
            image = result.scalar_one_or_none()
            if image is None:
                raise Exception("Image does not exist")
            return image

    return asyncio.run(_get_image(id))


def update_progress(image: GeneratedImage, step: int):
    async def _update_progress(image: GeneratedImage, step: int):
        async with async_session_maker() as session:
            image.progress = int((step / image.num_steps) * 100)
            session.add(image)
            await session.commit()

    asyncio.run(_update_progress(image, step))


def update_file_name(image: GeneratedImage, file_name: str):
    async def _update_progress(image: GeneratedImage, file_name: str):
        async with async_session_maker() as session:
            image.file_name = file_name
            session.add(image)
            await session.commit()

    asyncio.run(_update_progress(image, file_name))


@dramatiq.actor()
def text_to_image_task(image_id: int):
    image = get_image(image_id)

    def callback(step: int, _timestep, _tensor):
        update_progress(image, step)

    image_output = text_to_image_middleware.text_to_image.generate(
        image.prompt,
        negative_prompt = image.negative_prompt,
        num_steps = image.num_steps,
        callback = callback,
    )

    file_name = f"{uuid.uuid4()}.png"
    storage = Storage()
    storage.upload_image(image_output, file_name, settings.storage_bucket)
    update_file_name(image, file_name)
