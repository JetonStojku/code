# this recursive function the calc working days after includin public holidays returning the date after.
# example if today is monday 18.04.2022 and we want date 7 woking days after but we have monday, tuesday public holidays this function return 22.04.2022
def calc_day_after(self, date_from, day_after):
    if day_after <= 0:
        return date_from
    else:
        date_to = date_from + relativedelta(days=day_after)
        day_extra = self.search_count([('date', '>=', date_from), ('date', '<=', date_to)])
        return self.calc_day_after(date_to, day_extra)
