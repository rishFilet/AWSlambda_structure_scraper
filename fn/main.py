import utils
from site_one import SiteOne
from site_two import SiteTwo
import os


def handler(event, context):
    if os.getenv("binary_path") is None and os.getenv("executable") is None:
        os.environ["binary_path"] = "/opt/chrome/headless-chromium"
        os.environ["executable"] = "/opt/chrome/chromedriver"
    site = event['site']
    test_run = bool(int(event['test_run']))
    master_list_file = '{}_master_list.json'.format(site)
    master_show_objects = []
    site_dict = {"{}".format(site): []}
    if site == "site1":
        s1 = SiteOne()
        categories = ["sports", "entertainment"]
        for cat in categories:
            print("\nScraping started for {} in category {}".format(site, cat))
            site1_master_list = s1.get_items_in_channels(cat, test_run)
            print("Scraping logos for {} in category {}".format(site, cat))
            site1_channel_logos_list = s1.get_logos(cat)
            if cat == "sports":
                genre = cat
            else:
                genre = None
            print("Converting scraped data to JSON format")
            all_show_objects = utils.convert_scraped_data_to_json_site_one(
                site1_master_list, genre, site1_channel_logos_list)
            site_dict[site].extend(all_show_objects)
        s1.sel_obj.stop_driver()
    if site == "site2":
        site = event['site']
        s2 = SiteTwo()
        print("\nScraping started for {}".format(site))
        site2_master_list = s2.get_items_in_channels(test_run)
        all_show_objects = utils.convert_scraped_data_to_json_site_two(
            site2_master_list)
        site_dict[site].extend(all_show_objects)
        s2.sel_obj.stop_driver()
    #utils.write_master_list_json(site_dict, "{}_test_data_before_master_list.json".format(site), site)
    print("Converting master list to show Objects..Final Step!")
    show_objects = utils.convert_master_list_to_show_obj(
        site_dict, site)
    master_show_objects.extend(show_objects)
    if event['output'] == 'lambda':
        return master_show_objects
    else:
        print("Outputting all json data to file: {}".format(master_list_file))
        utils.write_master_list_json(
            master_show_objects, master_list_file, site)
    print("Scraping COMPLETE! Check logs for details")


if __name__ == "__main__":
    # Setting the environment variables for the chromedriver and headless-chromium
    os.environ["binary_path"] = os.getcwd()+"/venv/chrome/headless-chromium"
    os.environ["executable"] = os.getcwd()+"/venv/chrome/chromedriver"
    handler("site1", None)
    handler("site2", None)
