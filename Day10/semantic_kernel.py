import asyncio
import semantic_kernel as sk

from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments

kernel = sk.Kernel()

async def main():
    txt = kernel.import_plugin_from_object(TextPlugin(), "MyPlugin")

    arguments = KernelArguments(input="toys are very good")

    response = await kernel.invoke(
        txt["uppercase"],
        arguments=arguments
    )

    print(response)

asyncio.run(main())