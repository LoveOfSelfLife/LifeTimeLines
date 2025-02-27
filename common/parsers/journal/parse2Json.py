from daydata import DayData, parse_jrnl_data
import json

def gen_tags(day: DayData):
    tags = []
    if day.year % 2 != 0:
        tags.append('oddYear')
    if day.month % 2 != 0:
        tags.append('oddMonth')
    if day.get_day_of_week() % 2 != 0:
        tags.append('oddDayOfWeek')
    if day.day % 2 != 0:
        tags.append('oddDay')
    return tags
    

def expand_day_to_items(day: DayData):
    indx = 0
    current_date_str = day.get_date_str()
    current_date_int = day.get_date_int()
    tags = gen_tags(day)
    for item in day.items:
        day_item = dict()
        day_item["id"] = f'{current_date_str}_{str(indx)}'
        day_item["date_dtr"] = current_date_str
        day_item["seq_i"] = indx
        day_item["total_seq_i"] = current_date_int + indx
        day_item["year_i"] = day.year
        day_item["month_i"] = day.month
        day_item["day_i"] = day.day
        day_item["day_of_week_i"] = day.get_day_of_week()
        day_item["day_of_week_name_s"] = day.get_day_of_week_str()
        day_item["day_of_month_i"] = day.day
        day_item["week_of_year_i"] = day.get_week_of_year()
        if tags:
            for t in tags:
                day_item[f'day_{t}_b'] = True

        if item.type == "TXT":
            day_item["content_t"] = ". ".join(item.text_items) 
            if item.time:            
                day_item['time_s'] = item.time
        
        item_type = 's'
        val1='.'
        if item.type == "KEY":
            if item.key in ['B', 'S', 'L', 'D']:
                item_type = 't'
            if item.key_val:
                val1 = item.key_val
            day_item[f'key_{item.key}_{item_type}'] = f'{val1}'                

            if item.key_val_list:
                val2 = f'{item.key_val_list}'
                day_item[f'keylist_{item.key}_{item_type}'] = f'{val2}'
        yield day_item
        indx = indx + 1

def journal_to_json(infd, outfd):
    day_list = parse_jrnl_data(infd)
    print('[', file=outfd)
    print_delimeter = False
    for day in day_list:
        for dayitem in expand_day_to_items(day):
            if print_delimeter:
                print(',', file=outfd)
            else:
                print_delimeter = True
            print(json.dumps(dayitem, indent=4, default=lambda x: x.__dict__), file=outfd)
    print(']', file=outfd)
            
if __name__ == '__main__':

    infile = "/Users/richk/GoogleDrive/me/ALL.txt"
    outfile = "/Users/richk/GoogleDrive/me/ALL2Z.json"
    with open(infile, "r") as inf:
        with open(outfile, "w") as outf:
            journal_to_json(inf, outf)
