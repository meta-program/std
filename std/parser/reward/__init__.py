
# support numpy/torch 
def reward_score(reward, score):
    lt_zero = score < 0
    mask = ~lt_zero.any(-1, keepdims=True)
    # no need to zero out if reward < 0 or all the rule scores are nonnegative
    reward_mask = (reward < 0) | mask.squeeze(-1)
    score_mask = lt_zero | mask
    # effectively zero out all the positive score if any of the scores should be negative
    return reward * reward_mask + (score * score_mask).sum(-1)
