process MERGE_PREDICTIONS {
    label 'process_low'
    tag "${metadata.sample}"

    conda "bioconda::mhcgnomes=1.8.4"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcgnomes:1.8.4--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcgnomes:1.8.4--pyh7cba7a3_0' }"

    input:
    tuple val(metadata), path(prediction_files), path(input_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: merged
    path "versions.yml", emit: versions

    script:
    """
    merge_prediction_outputs.py \
        --sample_id '${metadata.sample}' \
        --prediction_files '${prediction_files}' \
        --input_file '${input_file}' \
        --file_type '${metadata.file_type}'


    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
        mhcgnomes \$(python -c "from mhcgnomes import version; print(version.__version__)"   )
    END_VERSIONS
    """
}
