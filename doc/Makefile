.PHONY: all clean

all: mudblood.html

clean:
	rm -f *.html

mudblood.html: docbook.xml
	xsltproc -o mudblood.html /usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/docbook.xsl docbook.xml
