# Code-Completion-Kotlin-task

## Data collection

To collect data, I used the [kopyt](https://github.com/mvisat/kopyt) library. 
However, it lacked the capability to parse docstrings.
I made some modifications to enable this functionality. 
The result can be found in the directory `data_collection/kopyt/`.


I chose [kotlin](https://github.com/JetBrains/kotlin) repository for parsing. 
To parse another repository, you need to replace the link in `data_collection/config.json`.

To run: 
`python3 data_collection/data_collection.py`


Altogether, I collected a total of 70,248 examples. 
Among these, only 5,369 contained non-empty docstrings and function bodies. 
Plots illustrating the length distribution of these examples can be found in `dataset_analysis.ipynb`. 
For fine-tuning I used the shortest 80% of these examples.

## Fine-tune

Phi-1.5 has 1.3 billion parameters, which is quite difficult fine-tune with a small amount of resources. 
Due to constraints of free Google Colab I had to use LoRA library. 
For this step I used the following [tutorial](https://gathnex.medium.com/consumer-friendly-fine-tuning-with-microsoft-phi-1-5-4bd28ad18af7).

Code can be found and run in `finetune.ipynb`.

## Evaluation
 

For evaluation 2 metrics were used:

- Edit similarity (if T is the total number of elements in both sequences, and M is the number of matches, edit_sim is 2.0*M / T)
- BLEU (Bilingual Evaluation Understudy)

Both implementations were taken from [CodeXGLUE -- Method Generation repository](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Method-Generation).

## Results

Unfortunately, even when using LoRA, I managed to use only 200 examples out of more than 5,000 collected for training. 
For a model of this size, this is too small to get a convincing result.

However, even with such a small amount of data, you can notice a slight improvement in both metrics for kotlin. 
BLEU increased from 36.0 to 36.53. Edit sim decreased from 46.12 to 45.69.

It is worth noting that I have set the maximum number of new tokens to 200. 
Despite the fact that if you take 100, the metrics are significantly higher (by about 10%), most of the examples from both datasets have a length of up to 200 tokens.

As we can see, for example, from cases in python that have improved according to the BLEU metric, the result does not look particularly reasonable. 
I think it would be interesting to look at some metric that determines how similar a given piece of code is to a particular language. 
It would also be worth looking at the CodeBLUE metric, that can consider the grammatical and the logic correctness, leveraging the abstract syntax tree and the data-flow structure.