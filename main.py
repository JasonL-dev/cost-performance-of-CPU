import requests
import csv
import pandas as pd
import io
import re
from fake_useragent import UserAgent

# Crawl SPEC data
cpu_url_2017 = 'https://spec.org/cgi-bin/osgresults?conf=cpu2017;op=dump;format=csvdump'  # url

cpu_2017_content = requests.get(cpu_url_2017).content
cpu_2017_data = pd.read_csv(io.StringIO(cpu_2017_content.decode('ISO-8859-1')))

print('Crawl SPEC data successfully')


# Crawl price data
def get_price(row):
    # We search the price on 'itprice.com' for each CPU, and take the most frequent result as the unique price.
    headers = {
    'User-Agent': UserAgent().random}
    cpu_str = row['processor'].replace(' ', '%20')
    url = 'https://itprice.com/dell-price-list/' + cpu_str + '.html'
    content = requests.get(url, headers = headers).content
    price_list = re.findall('\$[(\d)|(\,)]+\.', str(content))
    if price_list and len(price_list) > 0:
        price = int(max(set(price_list), key=price_list.count
                       ).replace(',', '').replace('.', '').replace('$', ''))
        row["price"] = price
    else:
        row["price"] = 0
    return row


cpu_2017_data = cpu_2017_data.apply(get_price, axis=1)
print('Crawl price data successfully')

# Define column names
ads_cpu_2017 = cpu_2017_data[['processor', 'price', 'peak_result', 'base_result', 'cores', 'chips',
                             'enabled_threads _per_core', 'processor_mhz', 'parallelization', 'base_pointer_size',
                             'peak_pointer_size', '1st_level_cache', '2nd_level_cache', '3rd_level_cache', 'test_date']]

# Almost every CPU has been tested many times, I take the median 'base_result' as the test result
result = ads_cpu_2017.groupby("processor", as_index =False)["base_result"].quantile(q=0.5, interpolation='nearest')
result = result.merge(ads_cpu_2017, how='left', on = ['processor', 'base_result'])
# Drop the processor named 'redacted'
result = result.drop(result[result['processor'] == 'redacted'].index)
result = result.drop_duplicates(subset=['processor'], keep='first')
# Drop the data that we didn't crawl the price successfully
result = result.drop(result[result['price'] == 0].index)
# Format the test date as '2020-09'
result['test_date'] = pd.to_datetime(result['test_date'], format='%b-%Y')

# Output the result
result.to_csv('cost_performance_of_CPUs.csv')
