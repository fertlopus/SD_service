import torch
from diffusers import StableDiffusionPipeline
from collections.abc import Callable
from PIL import Image


class TextToImage:
    """
        A class to convert textual descriptions into images using the Stable Diffusion model.

        Attributes:
            pipeline (StableDiffusionPipeline | None): A pipeline for the Stable Diffusion model.
            repo_id (str): The identifier for the Stable Diffusion model repository.

        Methods:
            load_model():
                Loads the Stable Diffusion model into the pipeline attribute.

            generate(prompt, negative_prompt=None, num_steps=50, callback=None) -> Image.Image:
                Generates an image from a textual prompt using the Stable Diffusion model.

                Args: prompt (str): The text prompt to generate the image from.
                negative_prompt (str | None): A text prompt that describes what should not appear in the image.
                num_steps (int): The number of inference steps to run; higher values can lead to more detailed images.
                callback (Callable[[int, int, torch.FloatTensor], None] | None): An optional callback function
                                                                                 that is called at each inference step.

                Returns:
                    Image.Image: The generated image.

                Raises:
                    RuntimeError: If the pipeline is not loaded or not supported anymore.

        Example:
            >>> text_to_image = TextToImage()
            >>> text_to_image.load_model()
            >>> image = text_to_image.generate("A futuristic cityscape", num_steps=100)
            >>> image.show()
        """
    pipeline: StableDiffusionPipeline | None = None
    repo_id: str = "runwayml/stable-diffusion-v1-5"

    def load_model(self):
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        pipeline = StableDiffusionPipeline.from_pretrained(self.repo_id)
        pipeline.to(device)
        self.pipeline = pipeline

    def generate(self, prompt: str, *, negative_prompt: str | None = None, num_steps: int = 500,
                 callback: Callable[[int, int, torch.FloatTensor], None] | None = None) -> Image.Image:
        if not self.pipeline:
            raise RuntimeError("No pipeline provided or this version is not supported anymore.")
        return self.pipeline(
            prompt,
            negative_prompt = negative_prompt,
            num_inference_steps = num_steps,
            guidance_scale = 0.7,
            callback = callback,
            height = 800,
            width = 600
        ).images[0]


if __name__ == "__main__":
    text_to_image = TextToImage()
    text_to_image.load_model()

    def callback(step: int, _timestep, _tensor):
        print(f" ⚙ ️ Step {step}")

    image = text_to_image.generate(
        "The Milky Way picture as it was taken from the space.",
        negative_prompt="low quality, ugly, sharpen, from bird view, dark, old",
        callback=callback,
    )
    image.save("./src/generated/output.png")
