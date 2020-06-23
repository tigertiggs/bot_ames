# experimental cog that mainly serves as a playground for code stuff

import discord
from discord.ext import commands
import os, sys, json, traceback, datetime, requests

from bs4 import BeautifulSoup

class testCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.name = '[test]'

    @commands.command()
    async def test(self, ctx):
        s = requests.Session()
        url = "https://blueoath.miraheze.org/w/api.php"
        params = {
            "action":           "parse",
            "page":             "Saratoga",
            "prop":             "text",
            "formatversion":    "2",
            "format":           "json"
        }
        r = s.get(url=url, params=params)
        print(r.status_code)
        #print(r.text)
        data = r.json()
        html = data['parse']['text']
        soup = BeautifulSoup(html, 'html.parser')
        #print(soup.prettify())

        # navigating
        #print(soup.head)
        #print(soup.title)
        #print(soup.get_text)
        #print(html[:63])
        print(soup.table.th)

def setup(client):
    client.add_cog(testCog(client))

def test():
    s = requests.Session()
    url = "https://blueoath.miraheze.org/w/api.php"
    params = {
        "action":           "parse",
        "page":             "Saratoga",
        "prop":             "text",
        "formatversion":    "2",
        "format":           "json"
    }
    r = s.get(url=url, params=params)
    print("status code:", r.status_code)
    data = r.json()
    if data.get("error", None) != None:
        print(data["error"])
        return
    html = data['parse']['text']
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all("table")
    #print(len(tables))

    for table in tables:
        print(table.tbody.tr.text.encode("utf-8"))

    #read_stats_table(tables[0])
    #read_skills_table(tables[1])
    #read_traits_table(tables[2])
    #read_lb_table(tables[3])

    #read_gallery(soup.find_all("div", class_="tabs tabs-tabbox"))

    #print([p.text for p in soup.find_all("p")])

    s.close()

def read_stats_table(table):
    table_body = table.tbody.find_all("tr")

    # GENERAL STATS
    general_contents = table_body[:8]
    # name, class, faction
    print("name:",      general_contents[0].th.string.encode('utf-8'))
    temp = general_contents[1].find_all("td")
    print("class:",     temp[0].string)
    print("faction:",   temp[1].string)
    
    # portrait halfbody
    print("portrait:",  temp[2].div.a.img['src'])

    # stats - hp/armour/trpdef
    temp = general_contents[4].find_all("td")
    print("hp:", f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})")
    print("armour:", f"{temp[4].string if temp[4].string != '✕' else '???'}({temp[5].string if temp[5].string!= '✕' else '???'})")
    print("torp def:", f"{temp[7].string if temp[7].string != '✕' else '???'}({temp[8].string if temp[8].string != '✕' else '???'})")
    
    # stats aa/spd/fp
    temp = general_contents[5].find_all("td")
    print("aa:", f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})")
    print("spd:", f"{temp[4].string if temp[4].string != '✕' else '???'}")
    print("fp:", f"{temp[6].string if temp[6].string != '✕' else '???'}({temp[7].string if temp[7].string != '✕' else '???'})")

    # SPECICAL
    special_contents = table_body[6:-3]
    while True:
        if len(special_contents) == 0:
            break
        # try to get special category
        category = special_contents.pop(0).th.string

        if "Aviation" in category:
            print("SPEC: AVIATION")
            ava_spec = special_contents[:3]
            special_contents = special_contents[3:]

            # stats(cv) asp/ap/range
            temp = ava_spec[0].find_all("td")
            print("asp:", f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})")
            print("ap:", f"{temp[4].string if temp[4].string != '✕' else '???'}({temp[5].string if temp[5].string!= '✕' else '???'})")
            print("range:", temp[7].string)

            # stats(cv) db/ap
            temp = ava_spec[1].find_all("td")
            print("asp:", temp[1].string)
            print("ap:", temp[3].string)

            # stats(cv) tb/rld
            temp = ava_spec[2].find_all("td")
            print("tb:", temp[1].string)
            print("rld:", temp[3].string)

        elif "Shelling" in category:
            print("SPEC: SHELLING")
            shell_spec = special_contents.pop(0)

            # stats(sh) scd/rld/range
            temp = shell_spec.find_all("td")
            print("scd:", f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})")
            print("rld:", temp[4].string)
            print("range:", temp[6].string)
        
        elif "Torpedo" in category:
            print("SPEC: TORP")
            torp_spec = special_contents.pop(0)

            # stats(tp) trp/stk/range
            temp = torp_spec.find_all("td")
            print("trp:", f"{temp[1].string if temp[1].string != '✕' else '???'}({temp[2].string if temp[2].string != '✕' else '???'})")
            print("stk:", temp[4].string)
            print("range:", temp[6].string)

    # MISC
    misc_contents = table_body[-3:]
    # gacha/comment/va
    print("acquisition:", misc_contents[0].th.string.split(":")[-1].strip())
    print("comment:", misc_contents[1].td.string)
    print("va:", misc_contents[2].td.string)

def read_skills_table(table):
    table_body = table.tbody.find_all("tr")

    # Class Skill
    category = table_body.pop(0)
    print("class skill:", get_str(str(category.td.p)))

    # SKILLS
    for i, category in enumerate(table_body):
        contents = category.find_all("td")
        print(f"skill {i+1} name:", get_str("\n".join(str(contents[0]).split("<br/>")[-2:])).encode("utf-8"))
        print(contents[1].text.encode("utf-8"),"\n")

def read_traits_table(table):
    table_body = table.tbody.find_all("tr")
    for i, trait in enumerate(table_body):
        contents = trait.find_all("td")
        print(f"trait {i+1}:", contents[0].string)
        print(contents[1].text,"\n")

def read_lb_table(table):
    table_body = table.tbody.find_all("tr")
    
    for i, lb in enumerate(table_body):
        print("LB",i+1)
        print(get_str(str(lb.td)) if str(lb.td) != "<td></td>" else "No effect")

def get_str(string):
    for x in ["<p>", "</p>", "<td>", "</td>","<br/>"]:
        while x in string:
            if x != "<br/>":
                string = string.replace(x,"")
            else:
                string = string.replace("<br/>", "\n")
    return string

def read_gallery(tabbox):
    if not tabbox:
        return

    div_contents = tabbox[-1].div.find_all("div")

    for i, dv in enumerate(div_contents):
        print(f"image {i+1}", dv.a.img['src'])

def get_index():
    s = requests.Session()
    url = "https://blueoath.miraheze.org/w/api.php"
    params = {
        "action":           "parse",
        "page":             "Senki",
        "prop":             "text",
        "formatversion":    "2",
        "format":           "json"
    }
    r = s.get(url=url, params=params)
    print("status code:", r.status_code)
    data = r.json()
    if data.get("error", None) != None:
        print(data["error"])
        return
    html = data['parse']['text']
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all("table")

    main_index = tables[0]
    for i, row in enumerate(main_index.find_all("tr")[1:]):
        fields = row.find_all("td")
        #print(str(fields[0]).encode('utf-8'))
        print("senki", i+1)
        print("pic:", fields[0].img['src'])
        print("name(jp):", fields[1].text.replace("\n","").encode('utf-8'))
        print("name(en):", fields[2].text.replace("\n","").encode('utf-8'))
        print("class:", fields[3].text.replace("\n",""))
        print("rarity:", fields[4].text.replace("\n",""))
    
    s.close()


if __name__ == "__main__":
    #test()
    get_index()