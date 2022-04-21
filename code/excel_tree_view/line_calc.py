# this function work like excel to calc the year payslip for employes.
# examples are in photos
@api.onchange('line_ids')
def line_calc_onchange(self):
    self.total_calc_onchange()

    def formulas_to_list(rl_f):
        return re.findall('[a-zA-Z][a-zA-Z0-9]*\.balance', rl_f)

    for calc in self.line_ids.filtered(lambda x: x.formulas):
        f_list = formulas_to_list(calc.code)
        for month in months:
            code = calc.code
            for f_code in f_list:
                replace_txt = "sum(self.line_ids.filtered(lambda x: x.code == '{}').mapped('{}'))".format(f_code[:-8], month[0])
                code = code.replace(f_code, replace_txt)
            fields_text = "calc.{}".format(month[0])
            exec_text = '{} = {}'.format(fields_text, code)
            exec(exec_text)
