import requests
from bs4 import BeautifulSoup
import json
import time

def main():

    # #LOT OF RECIPES
    # URL = "https://www.kotikokki.net/reseptit/kategoria/paaruoat?categoryAlias=maincourse&sortBy=relevancy&currentPage=1"
    # page = requests.get(URL)
    # soup = BeautifulSoup(page.content, "html.parser")
    # result = soup.find("a", {"class" : "recipe-actions background-gradient"}).get("href")
    # print(result)
    #result = soup.find_all("li", {"class" : "recipe-item"})
    # print(result)

    #daily recipes
    URL = "https://www.kotikokki.net/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    result = soup.find_all("li", {"class" : "recipe-item dailyrecipe"})
    result = soup.find_all("li", {"class" : "recipe-item"})

    # find the ahref from recipe image. Works for all recipe links/images
    a_hrefs = []
    for li in result[:20:]:
        a_href = li.find("a", {"class" : "recipe-actions background-gradient"}).get("href")
        a_hrefs.append(a_href)

    cleaned_urls = []
    for href in a_hrefs:
        prefix = "www.kotikokki.net"
        recipe_url = "https://" + prefix + href
        cleaned_urls.append(recipe_url)
        print(recipe_url)

    recipes = []
    for url in cleaned_urls:
        time.sleep(1)
        # dont wanna be rude with insane requests
        recipe = parse_recipe(url)

        if recipe:
            recipes.append(recipe)

    list_of_dicts_to_json_file(recipes)

# parses one ecipe from recipe page of kotikokki.
# Argument: "url" is string to the recipe page.
# Return: object/dictionary with recipe details
def parse_recipe(url):

    recipe_dict = {}

    page_url = requests.get(url)
    soup_2 = BeautifulSoup(page_url.content, "html.parser")

    #recipe name
    recipeName = soup_2.find("span", {"class" : "fn"}).getText().capitalize()

    # we need portions estimate
    portions_cleaned = parse_portion(soup_2)
    if portions_cleaned == "":
        return None

    tags_cleaned = parse_recipe_tags(soup_2)
    if tags_cleaned == "":
        return None

    
    cookTime_cleaned = parse_cooktime(soup_2)

    ingredients_cleaned = parse_ingredients(soup_2)
    if ingredients_cleaned == "":
        return None

    result = soup_2.find("span", {"itemprop" : "recipeInstructions"})
    recipeDescription_clean = result.getText()

    #recipe description Should work for all recipe pages
    # description = soup_2.find("span", {"itemprop" : "recipeInstructions"})
    # paras_in_description = description.find_all("p")

    recipe_dict["recipeName"] = recipeName
    recipe_dict["mealCount"] = portions_cleaned
    recipe_dict["cookTime"] = cookTime_cleaned
    recipe_dict["activeCookTime"] = cookTime_cleaned
    recipe_dict["ingredientNames"] = ingredients_cleaned
    recipe_dict["recipeDescription"] = recipeDescription_clean
    recipe_dict["recipeTags"] = tags_cleaned

    return recipe_dict


def parse_portion(soup):
        portions_unclean = soup.find("span", {"class" : "yield"})
        if portions_unclean:
            portions_cleaned = portions_unclean.getText().split()[0]
        else:
            # we need some default value for portions count
            portions_cleaned = "4"

        return portions_cleaned

def parse_cooktime(soup):
    cookTime_unclean = soup.find("span", {"class" : "duration"})

    #cook time can be missing
    if not cookTime_unclean:
        cookTime_cleaned = ""
        return cookTime_cleaned

    cookTime_cleaned = cookTime_unclean.getText()
    cookTime_parts = cookTime_unclean.getText().split(" ")
    print(cookTime_parts)


    #cook time can have word "under" or "over". We want to remove those.
    removeable_word = None
    for word in cookTime_parts:
        if word.lower() in ["alle", "yli"]:
            removeable_word = word
            break

    if removeable_word:
        cookTime_parts.remove(removeable_word)

    #converting hours to minutes
    new_cookTime_parts = []
    if "h" == cookTime_parts[-1]:
        for item in cookTime_parts:
            if item.isdigit():
                new_item = str(int(float(item) * 60))
            elif ',' in item:
                new_item = item.replace(",", ".")
                new_item = str(int(float(new_item) * 60))
            elif item.lower() == "h":
                new_item = "min"
            else:
                new_item = item

            new_cookTime_parts.append(new_item)
    else:
        new_cookTime_parts = cookTime_parts

    # modify ranges to form (10-15 min
    if "-" == cookTime_parts[1]:
        cookTime_cleaned = "".join(new_cookTime_parts[:3])
    else:
        new_cookTime_parts = cookTime_parts
        cookTime_cleaned = " ".join(new_cookTime_parts)

    cookTime_cleaned = cookTime_cleaned.replace(" min", "")
    print(cookTime_cleaned)
    return cookTime_cleaned

def parse_ingredients(soup):
    ingredients = soup.find_all("tr", {"class" : "ingredient"})

    units_list = ["ml", "dl", "l", "tl", "rkl", "g", "prk", "rasia"]

    ingredientNames = []
    for ingredient in ingredients:
        ingredient_name_unclean = ingredient.find("span", {"data-view-element" : "name"})
        amount_unclean = ingredient.find("span", {"data-view-element" : "amount"})
        unit_unclean = ingredient.find("span", {"data-view-element" : "unit"})


        # ingredient name cleaning
        if ingredient_name_unclean:
            ingredient_name_clean = ingredient_name_unclean.getText().lower()
        else:
            continue;

        # ingredient amount handling
        if amount_unclean:
            amount_clean = clean_ingredient_amount(amount_unclean.getText())
        else:
            amount_clean = ""

        #units list not complete
        units_list = ["ml", "dl", "l", "tl", "rkl", "g", "kpl", "prk", "rasia", "ripaus", "pss"]
        if unit_unclean:
            unit_clean = unit_unclean.getText()
        else:
            unit_clean = ""


        #we dont want subheaders or such randomlines without no actual ingredients
        sub_headers_exist = any(substring in ingredient_name_clean.lower() for substring in ["koriste", "täyte", "pohja"])
        amount_and_unit_is_not_found = (unit_clean == "" and amount_clean == "")

        if sub_headers_exist and amount_and_unit_is_not_found:
            continue


        ingredient_dict = {}
        ingredient_dict["amount"] = amount_clean
        ingredient_dict["name"] = ingredient_name_clean
        ingredient_dict["unit"] = unit_clean

        ingredientNames.append(ingredient_dict)
    #eliminate recipes with ingredients without any amount information
    if all([dict["amount"] == "" for dict in ingredientNames]):
        return ""


    return ingredientNames

#string with ingredient amount
def clean_ingredient_amount(amount):

    # TODO. Better option to handle 7-8 amounts. Now just chosen for simplicity to take the smaller number, i.e. 7
    if "-" in amount:
        i = amount.find("-")
        amount = amount[:i]


    # decimal dot is needed
    if "," in amount:
        amount = amount.replace(",", ".")


    #handling decimals correctly (i.e. 2½ should be 2.5 and ½ should be 0.5)
    if "½" in amount:
        amount = amount.replace("½", "0.5")
        i = amount.find("0.5")
        if i > 0:
            amount = amount[:i] + ".5"
    elif "1/2" in amount:
        amount = amount.replace("1/2", "0.5")
        i = amount.find("0.5")
        if i > 0:
            amount = amount[:i] + ".5"

    if "1/4" in amount:
        amount = amount.replace("1/4", "0.25")
        i = amount.find("0.25")
        if i > 0:
            amount = amount[:i] + ".25"

    return amount

def parse_recipe_tags(soup):

    unwanted_recipe_tags = ['Jälkiruoat', 'Pizzat', 'Säilöntä', 'Makeat leivonnaiset',
        'Juomat', 'Välipalat']

    tags_unclean = soup.find("div", {"class" : "recipe-catagory-tags-container"}).getText()

    for unwanted_tag in unwanted_recipe_tags:
        if unwanted_tag in tags_unclean:
            return ""
    
    tags = tags_unclean.split(" ")
    tags_2 = []
    for tag in tags:
        tag = tag.replace("\n", "")
        if tag == "":
            continue
        tags_2.append(tag)

    # TODO some random shit in [0] slot
    if tags_2:
        return tags_2[1:]

#dump list of dictionaries to json data and to a file.
# Argument: takes list of dictionaries
# Returns: Nothing. Creates a json file.
def list_of_dicts_to_json_file(list_of_dicts):

    with open("recipe_data.json", "w", encoding='utf8') as filename:
        json.dump(list_of_dicts, filename, ensure_ascii=False)

main()
