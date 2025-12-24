# /setup_TreeTagger.sh

# -------------------------------
#         Terminal colors
# -------------------------------

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== TreeTagger Setup Script (Clean & Minimal) ===${NC}"

INSTALL_DIR="./.TreeTagger"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR" || { echo -e "${RED}Failed to enter install directory.${NC}"; exit 1; }

# -------------------------------
#  Download function with checks
# -------------------------------
download_file() {
    URL=$1
    FILE=$2
    echo -e "${GREEN}Downloading $FILE...${NC}"
    wget -c "$URL" -O "$FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to download $FILE. Exiting.${NC}"
        exit 1
    fi
}

# -------------------------------
#           Downloads
# -------------------------------
download_file "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.5.tar.gz" "tree-tagger-linux-3.2.5.tar.gz"
download_file "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz" "tagger-scripts.tar.gz"
download_file "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz" "german.par.gz"
download_file "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz" "english.par.gz"

# -------------------------------
#       Extract archives
# -------------------------------
echo -e "${GREEN}Extracting archives...${NC}"
tar -xzf tree-tagger-linux-3.2.5.tar.gz
tar -xzf tagger-scripts.tar.gz

# -------------------------------
#    Decompress parameter files
# -------------------------------
echo -e "${GREEN}Decompressing parameter files...${NC}"
gzip -d german.par.gz
gzip -d english.par.gz

# -------------------------------
#    Move param files to lib/
# -------------------------------
mkdir -p lib
mv german.par lib/
mv english.par lib/
echo -e "${GREEN}Parameter files moved to lib/${NC}"

# -------------------------------
# Cleanup unnecessary files & folders
# -------------------------------
echo -e "${GREEN}Cleaning up unnecessary files...${NC}"

rm -f tree-tagger-linux-3.2.5.tar.gz tagger-scripts.tar.gz

# Remove extra files/folders
rm -f FILES README.script Release-Notes
rm -rf doc

echo -e "${BLUE}=== TreeTagger setup completed! ✅ ===${NC}"

#      /\_/\  
#     ( o.o )  <WOOF>
#      > ^ <  