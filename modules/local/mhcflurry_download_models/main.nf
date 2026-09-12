process MHCFLURRY_DOWNLOAD_MODELS {
    label 'process_single'

    // conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcflurry:2.1.4--pyh7e72e81_1' :
        'quay.io/biocontainers/mhcflurry:2.1.4--pyh7e72e81_1' }"

    output:
    path "mhcflurry-data", emit: models
    path "versions.yml"  , emit: versions

    script:
    """
    export MHCFLURRY_DATA_DIR=./mhcflurry-data
    export MHCFLURRY_DOWNLOADS_CURRENT_RELEASE=2.2.0

    # A fetch interrupted mid-extraction leaves a partial dir that mhcflurry treats as downloaded, so check for weights.csv
    models=\$MHCFLURRY_DATA_DIR/\$MHCFLURRY_DOWNLOADS_CURRENT_RELEASE/models_class1_presentation
    for attempt in 1 2 3; do
        [ -f "\$models/models/weights.csv" ] && break
        rm -rf "\$models"
        mhcflurry-downloads fetch models_class1_presentation || sleep 30
    done
    [ -f "\$models/models/weights.csv" ] || { echo "MHCflurry model download failed" >&2; exit 1; }

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        \$(mhcflurry-predict --version | cut -d' ' -f2)
    END_VERSIONS
    """

    stub:
    """
    mkdir -p mhcflurry-data/2.2.0/models_class1_presentation/models
    touch mhcflurry-data/2.2.0/models_class1_presentation/models/weights.csv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        \$(mhcflurry-predict --version | cut -d' ' -f2)
    END_VERSIONS
    """
}
