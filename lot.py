# Copyright Google

# BSD License

import argparse
import csv
import datetime

class Lot(object):
  """Represents a buy with optional sell."""
  def __init__(self, count, symbol, description,
               buydate, basis,
               selldate = None,
               code = None,
               adjustment = None,
               proceeds = None,
               form_position = '',
               buy_lot = '',
               is_replacement = False):
    self.count = count
    self.symbol = symbol
    self.description = description
    self.buydate = buydate
    self.basis = basis
    # These may be None if it's just a buy:
    self.selldate = selldate
    self.code = code
    self.adjustment = adjustment
    self.proceeds = proceeds
    self.form_position = form_position
    self.buy_lot = buy_lot
    self.is_replacement = is_replacement

  @staticmethod
  def str_to_float(f):
    if f.startswith('$'): f = f[1:]
    f = f.replace(',', '')
    if f == '': f = '0'
    return float(f)

  @staticmethod
  def create_from_csv_row(row, buy_lot):
    if len(row) > 10 and row[10]:
      buy_lot = row[10]
    lot = Lot(int(row[0]), row[1], row[2],
              datetime.datetime.strptime(row[3].strip(), "%m/%d/%Y").date(),
              Lot.str_to_float(row[4]), buy_lot=buy_lot)
    if row[5]:
      lot.selldate = \
        datetime.datetime.strptime(row[5].strip(), "%m/%d/%Y").date()
      lot.proceeds = Lot.str_to_float(row[6])
      lot.code = row[7]
      lot.adjustment = Lot.str_to_float(row[8])
    lot.form_position = row[9]
    is_replacement = False
    if len(row) > 11:
      is_replacement = not (row[11].lower() != 'true')
    lot.is_replacement = is_replacement
    return lot
  def acquition_match(self, that):
    return (self.count == that.count and
            self.symbol == that.symbol and
            self.description == that.description and
            self.buydate == that.buydate and
            self.basis == that.basis)
  def has_sell(self):
    return self.selldate is not None
  @staticmethod
  def csv_headers():
    return ['Cnt', 'Sym', 'Desc', 'BuyDate',
            'Basis', 'SellDate', 'Proceeds', 'AdjCode',
            'Adj', 'FormPosition', 'BuyLot', 'IsReplacement']
  def csv_row(self):
    return [self.count, self.symbol, self.description,
            self.buydate.strftime('%m/%d/%Y'),
            self.basis,
            None if self.selldate is None else \
            self.selldate.strftime('%m/%d/%Y'),
            self.proceeds, self.code,
            self.adjustment, self.form_position,
            self.buy_lot, 'True' if self.is_replacement else '']
  def __eq__(self, that):
    if not isinstance(that, self.__class__):
      return False
    return self.__dict__ == that.__dict__
  def __ne__(self, that):
    return not self.__eq__(that)
  def __str__(self):
    front = ("%2d %s (%s) acq: %s %8.02f" %
             (self.count, self.symbol, self.description,
              self.buydate, self.basis))
    sell = ""
    code = ""
    if self.selldate:
      sell = (" sell: %s %8.02f" %
              (self.selldate, self.proceeds))
    if self.code or self.adjustment:
      if self.adjustment:
        code = " [%1s %6.02f]" % (self.code, self.adjustment)
      else:
        code = " [%1s]" % (self.code)
    position = ''
    if self.form_position:
      position = " " + self.form_position
    replacement = ''
    if self.is_replacement:
      replacement = ' [IsRepl]'
    return front + sell + code + position + ' ' + self.buy_lot + replacement
  __repr__ = __str__

def save_lots(lots, filepath):
  # Write the lots out to the given file
  fd = open(filepath, 'w')
  writer = csv.writer(fd)
  writer.writerow(Lot.csv_headers())
  for lot in lots:
    writer.writerow(lot.csv_row())

def load_lots(filepath):
  reader = csv.reader(open(filepath))
  ret = []
  buy_num = 1
  for row in reader:
    if row[0] and row[0] == Lot.csv_headers()[0]:
      continue
    ret.append(Lot.create_from_csv_row(row, str(buy_num)))
    if ret[-1].buy_lot == str(buy_num):
      buy_num = buy_num + 1
  return ret

def print_lots(lots):
  print("Printing %d lots:" % len(lots))
  basis = 0
  proceeds = 0
  days = 0
  adjustment = 0
  # make sure all elements are unique
  id_list = [id(lot) for lot in lots]
  assert len(id_list) == len(set(id_list))
  # go through all lots
  for lot in lots:
    print(lot)
    basis += lot.basis
    if lot.proceeds:
      proceeds += lot.proceeds
    if lot.adjustment:
      adjustment += lot.adjustment
      if lot.adjustment != 0:
        assert(abs(lot.adjustment - (lot.basis - lot.proceeds)) < .0000001)
  print("Totals: Basis %.2f Proceeds %.2f Adj: %.2f (basis-adj: %.2f)" % (basis, proceeds, adjustment, basis - adjustment))
