# Stable Diffusion Service (SDS)

---

Architectural Pattern that is used to build a service: **[web-queue-worker](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/web-queue-worker)**

![img](./src/imgs/web-queue-worker.png)

---

#### Requirements:

---
* Python >= 3.10
* [Docker](https://www.docker.com/get-started/)
* Tranformers 

All the main dependencies and requirements are listed in `requirements.txt` file.

You can simply install all the dependencies via `pip`:

`python3 -m pip install -r requirements.txt`

It is recommended to have at least **16GB of RAM and dedicated GPU with at least 8GB VRAM**. 

For running the service you will also need **Redis server** on your local machine. The easiest way to run Redis is to use Docker container. 

Open terminal and run: 

`$ docker run -d --name worker-redis -p 6379:6379 redis`

After you will finish with exploration do not forget to stop the container

`$ docker stop worker-redis`

---

#### Worker for image generation task:

It is too resource consumable to run SD model directly via REST API server. The operation will take several minutes to consume a massive amount of memory and resources. To solve this, it is better to define another process, apart from server process, that will take care of this image generation task: **so called worker**. Its role to compute task in the background. 

Worker is a process running continuously in the background, waiting for incoming tasks. The tasks are sent by the server. Also we need a communication channel between the server and the worker. This role will take up the **queue**. It will accept and stack messages coming from the server and will make them available to read for the worker.

Schema:

![img](./src/imgs/server-queue-worker.png)

---
#### The Results of Stable Diffusion model:

Prompt:

`The Milky Way picture as it was taken from the space.`

Output:

![img](./src/generated/output.png)