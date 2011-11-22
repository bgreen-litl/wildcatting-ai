#!/usr/bin/env python


from wildcatting.theme import DefaultTheme


theme = DefaultTheme()
weeks = 10000
filename = 'oil_price_trend_data.txt'


def generate(weeks, f):
    for i in xrange(weeks):
        price = theme.getOilPrices().next()
        f.write('%s ' % price)
    f.write('\n')


if __name__ == '__main__':
    with open(filename, 'w') as f:
        generate(weeks, f)
