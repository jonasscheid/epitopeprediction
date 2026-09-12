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
    tuple val(meta), path("*_allele_input.json"), path("*_input.{csv,tsv}", arity: '1..*'), emit: prepared // arity: a single file must still arrive as a list
    path "versions.yml"                                                , emit: versions

    script:
    template "prepare_prediction_input.py"

    stub:
    def prefix  = task.ext.prefix ?: "${meta.id}"
    def entries = params.tools.tokenize(',').collect { tool ->
        def ext = tool == 'mhcflurry' ? 'csv' : 'tsv'
        """{"tool": "${tool}", "alleles": "HLA-A*01:01", "chunk_id": "", "alleles_input": "HLA-A*01:01", "filename": "${prefix}_${tool}_input.${ext}"}"""
    }
    """
    touch ${params.tools.tokenize(',').collect { tool -> "${prefix}_${tool}_input." + (tool == 'mhcflurry' ? 'csv' : 'tsv') }.join(' ')}
    echo '[${entries.join(',')}]' > ${prefix}_allele_input.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version 2>&1 | sed 's/Python //g')
        pandas: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('pandas').version)")
        mhcgnomes: \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('mhcgnomes').version)")
    END_VERSIONS
    """
}
