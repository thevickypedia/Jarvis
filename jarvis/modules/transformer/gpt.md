# Generative Pre-trained Transformer

### Warnings

- This module uses a pre-trained transformer to generate predictive responses.
- Due to the size of machine learning models, this feature will be disabled in limited mode.

### Requirements

**Minimum RAM availability**

- 8 GB to run the 7B models
- 16 GB to run the 13B models
- 32 GB to run the 33B models

### References

- Model Artifactory: https://ollama.com/library
- Alternatives: https://huggingface.co/meta-llama
- Supported Models: https://github.com/ollama/ollama/blob/main/README.md#model-library

### Model specific todos:

1. ~~[Customize prompt](https://github.com/ollama/ollama/blob/main/README.md#customize-a-prompt)~~
2. Support running in Docker containers
3. Write util scripts to,
    - ~~customize the model~~
    - build model and initiate server independently _(including docker)_
4. Add an option to host model on a remote server with an accessible endpoint
