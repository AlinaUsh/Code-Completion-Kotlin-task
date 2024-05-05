# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.
import os
import logging
import argparse
from fuzzywuzzy import fuzz
import json
import re
from bleu import _bleu

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def post_process(code):
    code = code.replace("<EOL>", "\n").replace("<INDENT>", " ").replace("<DEDENT>", " ")
    code = code.replace("<NUM_LIT>", "0").replace("<STR_LIT>", "").replace("<CHAR_LIT>", "")
    pattern = re.compile(r"<(STR|NUM|CHAR)_LIT:(.*?)>", re.S)
    lits = re.findall(pattern, code)
    for lit in lits:
        code = code.replace(f"<{lit[0]}_LIT:{lit[1]}>", lit[1])
    return " ".join(code.split())


def main():
    parser = argparse.ArgumentParser(description='Evaluate leaderboard predictions for code completion (line level).')
    parser.add_argument('--answers', '-a', required=True, help="filename of the labels, in txt format.")
    parser.add_argument('--predictions', '-p', required=True,
                        help="filename of the leaderboard predictions, in txt format.")
    args = parser.parse_args()

    preds = open(args.predictions, "r").readlines()
    gts = open(args.answers, "r").readlines()

    assert len(preds) == len(gts), f"Samples of predictions and answers are not equal, {len(preds)}: {len(gts)}"

    total = len(gts)
    edit_sim = 0.0
    edit_sim_list = []
    for pred, gt in zip(preds, gts):
        pred = post_process(pred.strip())
        gt = post_process(gt.strip())
        cur_ratio = fuzz.ratio(pred, gt)
        edit_sim += cur_ratio
        edit_sim_list.append(cur_ratio)

    bleu_score = round(_bleu(args.answers, args.predictions), 2)
    logger.info(f"Edit sim: {round(edit_sim / total, 2)}, BLEU: {bleu_score}")

    answers = []
    predictions = []
    with open(args.answers) as fh:
        for line in fh:
            answers.append(line.strip().split())
    with open(args.predictions) as fh:
        for line in fh:
            predictions.append(line.strip().split())

    resutls = []
    for ans, pred, edit_sim in zip(answers, predictions, edit_sim_list):
        cur_ans_file = 'cur_ans.txt'
        cur_pred_file = 'cur_pred.txt'
        ans = ' '.join(ans)
        pred = ' '.join(pred)
        with open(cur_ans_file, "w") as file:
            file.write(ans)
        with open(cur_pred_file, "w") as file:
            file.write(pred)
        bleu_score = round(_bleu(cur_ans_file, cur_pred_file), 2)
        resutls.append(
            {
                "answer": ans,
                "prediction": pred,
                "edit_sim": edit_sim,
                "bleu": bleu_score
            }
        )

    with open('results.json', 'w', encoding='utf-8') as f:
        json.dump(resutls, f)


if __name__ == "__main__":
    main()
