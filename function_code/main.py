import utils
from selenium_scraper import SeleniumScraper as sel_sc
from site_one import SiteOne

import time_util as tu


def handler(event, context):
    master_list_file = 'master_list.json'
    s1 = SiteOne()
    #s2 = SiteTwo()
    sites_to_scrape = [s1.site]
    for site in sites_to_scrape:
        site_dict = {"{}".format(site): "''"}
        if site == s1.site:
            categories = ["sports", "entertainment"]
        cat_dict = {}
        for cat in categories:
            print("\nScraping started for {} in category {}".format(site, cat))
            site1_master_list = s1.get_items_in_channels(cat, slider_test=True)
            print("Scraping logos for {} in category {}".format(site, cat))
            site1_channel_logos_list = s1.get_logos(cat)
            print("Getting genre/category on page")
            genre = s1.get_genre()
            print("Converting scraped data to JSON format")
            all_show_objects = utils.convert_scraped_data_to_json(
                site1_master_list, genre, site1_channel_logos_list)
            cat_dict[cat] = all_show_objects
        if site_dict[site] != "":
            site_dict[site] = cat_dict
        else:
            site_dict[site].update(cat_dict)
        s1.sel_obj.stop_driver()
    print("Outputting all json data to file: {}".format(master_list_file))
    utils.write_master_list_json(site_dict, master_list_file)
    print("Scraping COMPLETE! Check logs for details")

if __name__ == "__main__":
    handler(None, None)
    print("Scraping COMPLETE! Check logs for details")
