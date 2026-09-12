process PREPARE_PREDICTION_INPUT {
    label 'process_single'
    tag "${meta.id}"

    // conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcgnomes:1.8.6--pyh7cba7a3_0' :
        'biocontainers/mhcgnomes:1.8.6--pyh7cba7a3_0' }"

    input:
    tuple val(meta), path(tsv)
    path(supported_alleles_json)

    output:
    tuple val(meta), path("*_allele_input.json"), path("*_input.{csv,tsv}", arity: '1..*'), emit: prepared // arity keeps a single file a list for the flatMap
    path "versions.yml"                                                , emit: versions

    script:
    template "prepare_prediction_input.py"

    stub:
    def prefix     = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}_mhcflurry_input.csv
    touch ${prefix}_mhcnuggets_input.tsv
    echo '[{"tool": "mhcflurry", "alleles": "HLA-A*01:01", "chunk_id": "", "alleles_input": "HLA-A*01:01", "filename": "${prefix}_mhcflurry_input.csv"},
           {"tool": "mhcnuggets", "alleles": "HLA-A*01:01", "chunk_id": "", "alleles_input": "HLA-A01:01", "filename": "${prefix}_mhcnuggets_input.tsv"}]' > ${prefix}_allele_input.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
        mhcgnomes: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('mhcgnomes').version)")
    END_VERSIONS
    """
}
