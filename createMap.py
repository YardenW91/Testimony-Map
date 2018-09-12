import sys
import re
import codecs
import xml.etree.ElementTree as ET

testimony_file = sys.argv[1]
about_file = sys.argv[2]
# map of key: location name and info (sentences and coordinates)
locations = {}
# names of locations only
location_names = []
tree = ET.parse(testimony_file)
root = tree.getroot()

listOfRealLines = []
listOfLines = []

with open(testimony_file, 'r') as myfile:
    data = myfile.read().replace('\n', '')


# returns location name if in location_names, -1 otherwise
def find_location(myLocation):
    for loc in location_names:
        if loc.find(myLocation) != -1:
            return loc
    return -1


# extract text only from testimony
body_txt = re.match('(.*)<body>(.*)</body>(.*)', data).groups()[1]
body_txt = re.sub('</l>', "\n", body_txt)
body_txt = re.sub('<.*?>', '', body_txt)
body_txt = re.sub("\n","<br /><br />", body_txt)

with open(about_file, 'r') as aboutfile:
    about_txt = aboutfile.read().replace('\n', "<br />")

i = 0

for parent in root.iter():
    for child in parent:
        if child.tag.find('placeName') != -1:
            # first time location is mentioned
            if find_location(child.text) == -1:
                location_names.append(child.text)
                locations[child.text] = {}
                locations[child.text]["lon"] = child.attrib["role"].split(' ')[0]
                locations[child.text]["lat"] = child.attrib["role"].split(' ')[1]
                line = parent.text
                realLine = parent.text
                taggedLine = parent.text
                for c in parent:
                    i += 1
                    # line for info-window
                    line = line + "<a href=\"#A"+str(i)+"\">" + c.text + "</a>" + c.tail
                    realLine = realLine + c.text + c.tail
                    # line for testimony text
                    taggedLine = taggedLine + "<h id=\"A"+str(i)+"\">" + c.text + "</h>" + c.tail
                if line.find("Interviewer:") == -1:
                    if realLine not in listOfRealLines:
                        listOfRealLines.append(realLine)
                        listOfLines.append(line)
                        locations[child.text]["lines"] = line + "<br /><br />"
                    else:
                        locations[child.text]["lines"] = listOfLines[listOfRealLines.index(realLine)] + "<br /><br />"
                    body_txt = body_txt.replace(realLine, taggedLine)

                else:
                    # no need to add if this is a line the interviewer said
                    locations[child.text]["lines"] = ""

            else:
                # not first time location is mentioned
                line = parent.text
                taggedLine = parent.text
                realLine = parent.text
                for c in parent:
                    i += 1
                    # line for info-window
                    line = line + "<a href=\"#A"+str(i)+"\">" + c.text + "</a>" + c.tail
                    realLine = realLine + c.text + c.tail
                    # line for testimony text
                    taggedLine = taggedLine + "<h id=\"A"+str(i)+"\">" + c.text + "</h>" + c.tail
                if line.find("Interviewer:") == -1:
                    if realLine not in listOfRealLines:
                        listOfRealLines.append(realLine)
                        listOfLines.append(line)
                        locations[find_location(child.text)]["lines"] = locations[find_location(child.text)][
                                                                            "lines"] + line + "<br /><br />"
                    else:
                        # line has already appeared in a mention of a location earlier. pull the tagged line from before
                        # with the tags that were already given
                        if locations[find_location(child.text)]["lines"].find(listOfLines[listOfRealLines.index(realLine)]) == -1:
                            locations[find_location(child.text)]["lines"] = locations[find_location(child.text)][
                                                                            "lines"] + listOfLines[listOfRealLines.index(realLine)] + "<br /><br />"
                    body_txt = body_txt.replace(realLine, taggedLine)


# create an HTML file, a website with two tabs and a google map with info-windows
file = codecs.open("Testimony documentation.html", 'w')

file.write("<!DOCTYPE html>\n"
           "<html>\n"
           "<head>\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
           "<style>\n"
           "* {box-sizing: border-box}\n\n"
           "/* Set height of body and the document to 100% */\n"
           "body, html {\n"
           "    height: 100%;\n"
           "    margin: 0;\n"
           "    font-family: Arial;\n"
           "}\n\n"
           "/* Style tab links */\n"
           ".tablink {\n"
           "    background-color: #95A5A6;\n"
           "    color: black;\n"
           "    float: left;\n"
           "    border: none;\n"
           "    outline: none;\n"
           "    cursor: pointer;\n"
           "    padding: 14px 16px;\n"
           "    font-size: 17px;\n"
           "    width: 50%;\n"
           "}\n\n"
           ".tablink:hover {\n"
           "    background-color: #777;\n"
           "}\n\n"
           "/* Style the tab content (and add height:100% for full page content) */\n"
           ".tabcontent {\n"
           "    color: black;\n"
           "    display: none;\n"
           "    padding: 100px 20px;\n"
           "    height: auto;\n"
           "    min-height: 100% !important;\n"
           "}\n"
           "#Map {background-color: lightgray;}\n"
           "#About {background-color: lightblue;}\n"
           "</style>\n"
           "</head>\n"
           "<body>\n\n"
           "<button class=\"tablink\" onclick=\"openPage('Map', this, 'lightgray')\" id=\"defaultOpen\">Map</button>\n"
           "<button class=\"tablink\" onclick=\"openPage('About', this, 'lightblue')\">About</button>\n"
           "<div id=\"Map\" class=\"tabcontent\">\n"
           "  <p>\n")
#map
file.write("<h2 style=\"font-family:verdana;\"><center>Map of Family Journey</center></h2>\n\n"
           "<div id=\"googleMap\" style=\"width:100%;height:400px;\"></div>\n"
           "<script>\n"
           "function myMap() {\n"
           "var mapProp= {\n"
           "    center:new google.maps.LatLng(45.3883018,-35.1807992),\n"
           "    zoom:3,\n"
           "};\n"
           "var map=new google.maps.Map(document.getElementById(\"googleMap\"),mapProp);\n")
# add all locations to map, with info-window
for j in range(0, len(location_names)):
    i = str(j)
    file.write("var myPoint"+i+" = new google.maps.LatLng("+locations[location_names[j]]["lon"]+","+locations[location_names[j]]["lat"]+");\n"
               "var marker"+i+" = new google.maps.Marker({position: myPoint"+i+"});\n"
               "marker"+i+".setMap(map)\n")
    file.write("google.maps.event.addListener(marker"+i+", 'click', function() {\n")
    file.write("    var infowindow"+i+" = new google.maps.InfoWindow({\n")
    file.write("        content: \""+locations[location_names[j]]["lines"].replace('\"', '')+"\"\n")
    file.write("    });\n")
    file.write("infowindow"+i+".open(map, marker"+i+");\n")
    file.write("});")
# insert API key here!
file.write("}\n"
           "</script>\n\n"
           "<script src="
           "\"https://maps.googleapis.com/maps/api/js?key=INSERT-GOOGLE-API-KEY&callback=myMap\">\n"
           "</script>\n\n")

# add testimony and about text to tabs
file.write("<br /><h2>Testimony</h2>\n"
           "<br />"+body_txt+"</p>\n"
           "</div>\n\n"
           "<div id=\"About\" class=\"tabcontent\">\n"
           "  <h2 style=\"font-family:verdana;\"><center>About the project</center></h2>\n"
           "  <p>"+about_txt+"</p>\n"
           "</div>\n\n"
           "<script>\n"
           "function openPage(pageName,elmnt,color) {\n"
           "    var i, tabcontent, tablinks;\n"
           "    tabcontent = document.getElementsByClassName(\"tabcontent\");\n"
           "    for (i = 0; i < tabcontent.length; i++) {\n"
           "        tabcontent[i].style.display = \"none\";\n"
           "    }\n"
           "    tablinks = document.getElementsByClassName(\"tablink\");\n"
           "    for (i = 0; i < tablinks.length; i++) {\n"
           "        tablinks[i].style.backgroundColor = \"\";\n"
           "    }\n"
           "    document.getElementById(pageName).style.display = \"block\";\n"
           "    elmnt.style.backgroundColor = color;\n\n"
           "}\n"
           "document.getElementById(\"defaultOpen\").click();\n"
           "</script>\n\n"
           "</body>\n"
           "</html>\n")


