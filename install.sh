#!/bin/bash

SOURCE_PATH=$(dirname $(readlink -f $0))
DESTINATION_PREFIX="/usr/local"

# Check argument
if [ -n "$1" ];
then
    DESTINATION_PREFIX="${1%/}"
    echo
    while true; do
        read -p "Are you sure you want to install this program to '${DESTINATION_PREFIX}' prefix? " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
    echo
fi

# Check submodule
if [ ! -f ".gitmodules" ];
then
    echo "Error: File '.gitmodules' not found, please redownload source code."
    exit 1
fi

SUBMODULE_FILE=$(awk -F= '/^\spath/{print $2}' '.gitmodules')
SUBMODULE_MISSING="false"

if [ -z "${SUBMODULE_FILE}" ];
then
    echo "Error: Invalid '.gitmodules' file, please redownload source code."
    exit 1
fi

for LINE in ${SUBMODULE_FILE};
do
    if [ ! -f "${LINE}/__init__.py" ];
    then
        SUBMODULE_MISSING="true"
        echo "Error: Submodule '${LINE}' not found"
    fi
done

if [ "${SUBMODULE_MISSING}" == "true" ];
then
    echo "Error: Missing one or more submodules."
    echo "Please, use a Linux source release file or 'git clone --recurse-submodules'."
    exit 1
fi

# Set & check path
SHARE_PATH="${DESTINATION_PREFIX}/share"
APPLICATIONS_PATH="${SHARE_PATH}/applications"
BIN_PATH="${DESTINATION_PREFIX}/bin"
DESTINATION_PATH="${SHARE_PATH}/TinyPedal"

if [ ! -w "${SHARE_PATH}" -o ! -w "${BIN_PATH}" -o ! -w "${APPLICATIONS_PATH}" ];
then
    echo "Error: Insufficient privileges to install in prefix directory '${DESTINATION_PREFIX}' or it doesn't contain the required directories:"
    echo -e "    ${SHARE_PATH}, ${BIN_PATH}, ${APPLICATIONS_PATH}\n"
    exit 1
fi

# Remove old file & folder
if [ -d "${DESTINATION_PATH}" ];
then
    if [ -w "${DESTINATION_PATH}" ];
    then
        rm -r "${DESTINATION_PATH}"
    else
        echo "Error: Insufficient privileges to update existing install."
        exit 1
    fi
fi

rm "${APPLICATIONS_PATH}/TinyPedal-overlay.desktop" "${BIN_PATH}/TinyPedal"

# Write new file
BASE_FILE='
    run.py
    README.md
    LICENSE.txt
'
IMAGE_FILE='
    images/*.txt
    images/*.png
'

replace() {
    PATTERN="$1"
    STRING="$2"
    while read LINE; do
        echo "${LINE/${PATTERN}/${STRING}}"
    done
}

copyfiles() {
    for LINE in ${1}/*;
    do
        if [ -d "${LINE}" ];
        then
            # Create folder & copy content, exclude '__pycache__' folder
            if [[ "${LINE}" != *__pycache__* ]];
            then
                mkdir -p "${DESTINATION_PATH}/${LINE}"
                copyfiles "${LINE}"
            fi
        else
            # Copy file
            echo -n "."
            cp "${LINE}" "${DESTINATION_PATH}/${LINE}"
        fi
    done
}

# Copy desktop file
echo "Writing ${APPLICATIONS_PATH}/TinyPedal-overlay.desktop"
replace "/usr/local" "${DESTINATION_PREFIX}" <"${SOURCE_PATH}/TinyPedal-overlay.desktop" >"${APPLICATIONS_PATH}/TinyPedal-overlay.desktop"

# Copy launch script
echo "Writing ${BIN_PATH}/TinyPedal"
replace "./" "${DESTINATION_PATH}/" <"${SOURCE_PATH}/TinyPedal.sh" >"${BIN_PATH}/TinyPedal"
chmod a+x "${BIN_PATH}/TinyPedal"

# Copy base folder file
echo "Writing ${DESTINATION_PATH}"
mkdir -p "${DESTINATION_PATH}"
for LINE in ${BASE_FILE};
do
    cp "${LINE}" "${DESTINATION_PATH}"
done

# Copy images folder file
echo "Writing ${DESTINATION_PATH}/images"
mkdir -p "${DESTINATION_PATH}/images"
for LINE in ${IMAGE_FILE};
do
    cp "${LINE}" "${DESTINATION_PATH}/images"
done

# Copy submodule folder file
for LINE in ${SUBMODULE_FILE};
do
    echo "Writing ${DESTINATION_PATH}/${LINE}"
    mkdir -p "${DESTINATION_PATH}/${LINE}"
    cp "${LINE}/"*.{py,md,txt} "${DESTINATION_PATH}/${LINE}"
done

# Copy docs folder file
echo "Writing ${DESTINATION_PATH}/docs"
cp -r "docs" "${DESTINATION_PATH}/docs"

# Copy tinypedal folder file
echo "Writing ${DESTINATION_PATH}/tinypedal"
mkdir -p "${DESTINATION_PATH}/tinypedal"
copyfiles "tinypedal"

# Finish
echo -e "\nInstallation finished."
