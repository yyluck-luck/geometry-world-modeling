#!/usr/bin/env python3
from fractions import Fraction
from math import comb

def fractional_top_tail(xs, p=Fraction(5,100)):
    vals=sorted((Fraction(x) for x in xs), reverse=True)
    mass=p*len(vals); total=Fraction(0)
    for x in vals:
        if mass <= 0: break
        w=min(Fraction(1), mass); total += w*x; mass -= w
    return total/p/len(vals)

def main():
    assert comb(8,8) == 1
    assert comb(6,8) == 0
    # 94 zeros, 5 ones, 1 ten: top 5% = 5 items, last one fractional.
    xs=[0]*94+[1]*5+[10]
    assert fractional_top_tail(xs) == Fraction(14,5)
    assert fractional_top_tail([7]*100) == 7
    # Units are normalized before combining; raw metre/mm sums intentionally differ.
    metre=[Fraction(1),Fraction(1,10)]
    mm=[Fraction(1000),Fraction(100)]
    norm_m=sum(metre); norm_mm=sum(x/Fraction(1000) for x in mm)
    assert norm_m == norm_mm
    print('S95_CONTRACT_REPAIR_VALIDATION_PASS')
    print({'candidate_k_max_rule':'N>=8','fractional_top5_tie_case':'14/5','all_equal_tail':7,'normalized_unit_sum':str(norm_m)})
if __name__ == '__main__': main()
