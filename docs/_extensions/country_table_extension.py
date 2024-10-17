from docutils import nodes
from docutils.parsers.rst import Directive
import os
import json
from datetime import datetime

class ProductsTableDirective(Directive):
    has_content = True

    def run(self):
        env = self.state.document.settings.env
        json_path = os.path.join(env.srcdir, '../codegreen_core/utilities/country_list.json')

        # Read and parse the JSON file
        with open(json_path, 'r') as file:
            full_data = json.load(file)

        data = []
        for key in full_data["available"]:
            c = full_data["available"][key]
            data.append({"name": c["country"], "code":key  ,"source":c["energy_source"]}) 

        # Create a note node with the generation date
        note = nodes.note()
        paragraph = nodes.paragraph()
        date_str = datetime.now().strftime('%Y-%m-%d')
        paragraph += nodes.Text(f"The following table is automatically generated from 'codegreen_core.utilities.country_list.json' on {date_str}")
        note += paragraph


        list_node = nodes.bullet_list()
        for country in data:
            # Create a list item for the country
            list_item = nodes.list_item()
            paragraph = nodes.paragraph()
            paragraph += nodes.Text(f"{country['name']} (")
            paragraph += nodes.literal(text=country['code'])  # Inline code block for the country code
            paragraph += nodes.Text(f")")
            list_item += paragraph

            # Create a nested list for the "Source" item
            if 'source' in country:
                nested_list = nodes.bullet_list()
                nested_item = nodes.list_item()
                nested_paragraph = nodes.paragraph()
                nested_paragraph += nodes.Text(f"Energy source: {country['source']}")
                nested_item += nested_paragraph
                nested_list += nested_item
                list_item += nested_list

            # Add the country list item to the main list
            list_node += list_item
            
        return [note, list_node]

def setup(app):
    app.add_directive('country_table', ProductsTableDirective)
