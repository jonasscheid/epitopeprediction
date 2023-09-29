/*
* Copy non-free software provided by the user into the working directory
*/
process EXTERNAL_TOOLS_IMPORT {
    label 'process_low'

    conda "conda-forge::coreutils=9.1"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://containers.biocontainers.pro/s3/SingImgsRepo/biocontainers/v1.2.0_cv1/biocontainers_v1.2.0_cv1.img' :
        'biocontainers/biocontainers:v1.2.0_cv1' }"

    input:
    tuple val(toolname), val(toolversion), val(toolchecksum), path(tooltarball), file(datatarball), val(datachecksum), val(toolbinaryname)

    output:
    path "${toolname}", emit: nonfree_tools
    val  "v_*.txt", emit: versions

    script:
    """
    #
    # VALIDATE THE CHECKSUM OF THE PROVIDED SOFTWARE TARBALL
    #
    checksum="\$(md5sum "$tooltarball" | cut -f1 -d' ')"
    echo "\$checksum"
    if [ "\$checksum" != "${toolchecksum}" ]; then
        echo "Checksum error for $toolname. Please make sure to provide the original tarball for $toolname" >&2
        exit 2
    fi

    #
    # UNPACK THE PROVIDED SOFTWARE TARBALL
    #
    mkdir "${toolname}"
    tar -C "${toolname}" --strip-components 1 -x -f "$tooltarball"

    #
    # MODIFY THE NETMHC WRAPPER SCRIPT ACCORDING TO INSTALL INSTRUCTIONS
    # Substitution 1: We install tcsh via conda, thus /bin/tcsh won't work
    # Substitution 2: We want temp files to be written to /tmp if TMPDIR is not set
    # Substitution 3: NMHOME should be the folder in which the tcsh script itself resides
    #
    sed -i.bak \
        -e 's_bin/tcsh.*\$_opt/conda/bin/tcsh_' \
        -e "s_/scratch_/tmp_" \
        -e "s_setenv[[:space:]]NMHOME.*_setenv NMHOME \\`realpath -s \\\$0 | sed -r 's/[^/]+\$//'| sed -r 's/.\$//'\\`_ " "${toolname}/${toolbinaryname}"


    #
    # VALIDATE THE CHECKSUM OF THE DOWNLOADED MODEL DATA
    #
    if [ "$toolname" != "netmhciipan" ]; then
        checksum="\$(md5sum "$datatarball" | cut -f1 -d' ')"
        if [ "\$checksum" != "${datachecksum}" ]; then
            echo "A checksum mismatch occurred when checking the data file for ${toolname}." >&2
            exit 3
        fi
    fi

    #
    # UNPACK THE DOWNLOADED MODEL DATA
    #
    if [ "$toolname" != "netmhciipan" ]; then
        tar -C "${toolname}" -v -x -f "$datatarball"
    fi
    #
    # CREATE VERSION FILE
    #
    echo "${toolname} ${toolversion}" > "v_${toolname}.txt"

    """
}
