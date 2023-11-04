import asyncio
import uuid
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware.middleware import Middleware
from text_to_image import TextToImage


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
redis_broker = RedisBroker(host="localhost")
redis_broker.add_middleware(text_to_image_middleware)
dramatiq.set_broker(redis_broker)


# The worker configuration
# To run the service worker open terminal and type: $ dramatiq -p 1 -t 1 utils.worker
# -p is the number of processes and -t is the number of threads
@dramatiq.actor()
def text_to_image_task(prompt: str, *, negative_prompt: str | None = None, num_steps: int = 50):
    image = text_to_image_middleware.text_to_image.generate(
        prompt, negative_prompt=negative_prompt, num_steps=num_steps
    )
    image.save(f"{uuid.uuid4()}.png")
