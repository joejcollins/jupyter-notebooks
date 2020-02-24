''' Facade for the Azure vision and processing the response '''
from __future__ import unicode_literals # all strings are unicode
import json
import re
import requests
from package.secrets import Secrets

class Ocr(object):# pylint: disable=too-few-public-methods
    ''' Using the vision Api '''
    VISION_URL = "https://westeurope.api.cognitive.microsoft.com/vision/v1.0/"

    def __init__(self):
        pass

    @classmethod
    def image_to_json(cls, path_to_image):
        """ Get a Json response from the Ocr API"""
        ocr_url = cls.VISION_URL + "ocr"
        headers = {'Ocp-Apim-Subscription-Key': Secrets.COMPUTER_VISION_KEY}
        params = {'Content-Type': 'application/octet-stream'}
        image_file = {'media': open(path_to_image, 'rb')}
        print("Json Request for " + path_to_image)
        response = requests.post(ocr_url, headers=headers, params=params, files=image_file)
        parsed_json = json.loads(response.content)
        formatted_json = json.dumps(parsed_json, indent=2, sort_keys=True)
        return formatted_json

    @classmethod
    def get_lines(cls, path_to_json):
        """ Get the lines and their locations from the Ocr Json """
        with open(path_to_json) as json_file:
            unfiltered_json = json.load(json_file)
            lines = []
            for region in unfiltered_json['regions']:
                for line in region['lines']:
                    new_line = {}
                    bounding_box = line['boundingBox'].split(',')
                    new_line['x'] = int(bounding_box[0])
                    new_line['y'] = int(bounding_box[1])
                    new_line['width'] = int(bounding_box[2])
                    new_line['height'] = int(bounding_box[3])
                    text = ''
                    for word in line['words']: # concatenate the words into lines
                        text = text + " " + word['text']
                    text = text.strip()
                    new_line['text'] = text
                    lines.append(new_line)
                new_lines = {}
                new_lines['lines'] = lines
        return json.dumps(new_lines, indent=2, sort_keys=True)

    @classmethod
    def assemble_details(cls, path_to_json):
        """ Group the lines together that relate to one property 
        
        The lines in the Ocr Json are not obviously related to each other,
        however they have locations (measured from top left hand corner).
        So knowing where one piece of information is about a property should
        allow us to location the others.  All the vendors are prefixed 
        with 'Vendor:', this provides a key piece of information about the
        property and the other bits of information are located above and
        to the right of the vendor. """
        with open(path_to_json) as json_file:
            filtered_json = json.load(json_file)
        lines = filtered_json['lines']
        # 1. find the vendor lines
        vendors = [# Vendor = starts with "Vendor:" (this is the key land mark)
            line
            for line in lines
            if line['text'].startswith('Vendor: ')
        ]
        details = []
        for vendor in vendors:
            detail = {}
            detail['vendor_line'] = vendor['text']
            vendor_centre_x = vendor['x'] + (vendor['width']/2)
            # 2. find the address lines (above vendor line, maximum Y and don't start with "Vendor:")
            addresses = [ 
                line
                for line in lines
                if (line['x'] < vendor_centre_x and
                    line['y'] < vendor['y'] and
                    not line['text'].startswith('Vendor: '))
                ]
            address_line_above_y = max(address['y'] for address in addresses)# Get the Y value of the address directly above
            address_line = next(line for line in addresses if line['y'] == address_line_above_y)# get the address based on the Y value
            # Sometimes address line has been split so get the ones on that level so get the centre of the address line...
            address_line_centre_y = address_line['y'] + (address_line['height']/2)
            # ...and get the other lines at the same level (and not the address_line itself).
            other_parts_of_the_address = [
                line
                for line in addresses # select only from the address lines
                if (line['y'] < address_line_centre_y and
                    address_line_centre_y < (line['y'] + line['height']) and 
                    line['x'] > address_line['x']) # it is further to the right
                ]
            address_line['text'] += ' ' + ' '.join(address['text'] for address in other_parts_of_the_address)# and concatenate
            detail['address_line'] = address_line['text']
            # 3. find the house details (on same line as address and maximum X or over on the right)
            details_lines = [
                line
                for line in lines # select from all the lines
                if (line['y'] < address_line_centre_y and
                    address_line_centre_y < (line['y'] + line['height']) and 
                    line['x'] > address_line['x']) # it is further to the right
                ]
            details_line_furthest_right_x = max(details_line['x'] for details_line in details_lines)
            details_line = next(line for line in details_lines if line['x'] == details_line_furthest_right_x)
            detail['details_line'] = details_line['text']
            details.append(detail)
        return_string = json.dumps(details, indent=2, sort_keys=True)
        return return_string

    @classmethod
    def parse_details(cls, path_to_json):
        """ Pass in a file and return formatted json that looks like this: """
        return_string = """
{
 "details": [
   {
     "Title": "Miss",
     "FirstName": "Deliahla",
     "Initials": "D",
     "Surname": "Crump",
     "Phone": "07946123456",
     "Mobile": "",
     "Email": "deliahla@hotmail.co.uk",
     "Address1": "Flat 7",
     "Address2": "Elizabeth Court",
     "Address3": "Apple Square",
     "Town": "London",
     "Postcode": "SE48 2PE",
     "BedsRooms": 2,
     "ReceptionRooms": 1,
     "Bathrooms": 1
   },
   {
     "Title": "Ms",
     "FirstName": "Rhonda",
     "Initials": "R",
     "Surname": "Simpson",
     "Phone": "",
     "Mobile": "",
     "Email": "rhonda.simpson@gmail.com",
     "Address1": "212 Wombat House",
     "Address2": "Wigan Road",
     "Address3": "",
     "Town": "London",
     "Postcode": "SWIL 8AT",
     "BedsRooms": 1,
     "ReceptionRooms": 1,
     "Bathrooms": 1
   }
  ]
}
"""
        return return_string

    @classmethod
    def get_csv(cls, path_to_json):
        """ Measured from top left hand corner """
        with open(path_to_json) as json_file:
            filtered_json = json.load(json_file)
        lines = filtered_json['lines']
        vendors = [# Vendor = starts with "Vendor:" (this is the key land mark)
            line
            for line in lines
            if line['text'].startswith('Vendor: ')
        ]
        return_string = ""
        for vendor in vendors:
            # Vendor = starts with "Vendor:" (this is the key land mark)
            name = cls.__name_from(vendor)
            contact_details = cls.__contact_details_from(vendor)
            vendor_centre_x = vendor['x'] + (vendor['width']/2)
            # Address = Immediately above the vendors and don't start with "Vendor:"
            addresses = [# are 
                line
                for line in lines
                if (line['x'] < vendor_centre_x and
                    line['y'] < vendor['y'] and
                    not line['text'].startswith('Vendor: '))
            ]
            max_y = max(address['y'] for address in addresses)# this is the one directly above
            address_lines = [# sometimes address line has been split so get the ones on that level
                line['text']
                for line in addresses if line['y'] == max_y]
            address_csv = ' '.join(address for address in address_lines)# and concatenate
            post_code = address_csv.split(",", 4)[-1] # split to max 5 and keep the last one
            post_code = post_code.strip().upper().replace(",", "")
            address = cls.__address_from(address_csv)
            # The house details
            return_string += name + ", "
            return_string += address + ", "
            return_string += post_code + ", "
            return_string += contact_details + ",\n"
        return return_string.encode('utf-8', 'ignore')

    @classmethod
    def __name_from(cls, vendor):
        """ Get the name from the Vendor line """
        name = re.split("; |, ", vendor['text']) # use regex so splits with multiple delimiters
        name = name[0].replace('Vendor: ', '') # remove the Vendor tag
        return name

    @classmethod
    def __contact_details_from(cls, vendor):
        """ Get contact details from vendor """
        contact_details = re.split("; |, ", vendor['text'], 1) # split into 2
        if (len(contact_details) == 2):
            contact_details = contact_details[1] # contact details are the second part
            contact_details = contact_details.replace("Sold STC", "")
            contact_details = contact_details.replace("Valuer:", "")
            contact_details = contact_details.replace("T el:", "Tel:")
            contact_details = contact_details.replace("Tel.'", "Tel:")
            contact_details = contact_details.replace("Tel: ", "")
            contact_details = contact_details.replace("b:", "h:")
            contact_details = contact_details.replace(", ", "; ")
            contact_details = contact_details.strip()
        else: # there aren't any contact details
            contact_details = "No contact details"
        return contact_details

    @classmethod
    def __address_from(cls, address_csv):
        """ Tidy and pad the address """
        address = address_csv.split(",", 4)[:-1] # split to max 5 and dump the last one
        address[-1:-1] = [''] * (4 - len(address)) # pad to 4 elements just before the end
        address = ','.join(address)
        return address
