process SYFPEITHI {
    label 'process_single'
    tag "${metadata.sample}"

    conda "bioconda::epytope=3.1.0"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/epytope:3.1.0--pyh5e36f6f_0' :
        'quay.io/biocontainers/epytope:3.1.0--pyh5e36f6f_0' }"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:
    def prefix = "${metadata.sample}_${peptide_file.baseName}"
    def min_length = (metadata.mhc_class == "I") ? params.min_peptide_length_mhc_I : params.min_peptide_length_mhc_II
    def max_length = (metadata.mhc_class == "I") ? params.max_peptide_length_mhc_I : params.max_peptide_length_mhc_II

    """
    syfpeithi_prediction.py --input ${peptide_file} \\
        --alleles '${metadata.alleles}' \\
        --min_peptide_length ${min_length} \\
        --max_peptide_length ${max_length} \\
        --output '${prefix}_predicted_syfpeithi.tsv'
    echo ${peptide_file}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python \$(python --version | sed 's/Python //g')
        epytope \$(python -c "import pkg_resources; print(pkg_resources.get_distribution('epytope').version)")
        syfpeithi \$(python -c "from epytope.EpitopePrediction import EpitopePredictorFactory; print(EpitopePredictorFactory('syfpeithi').version)")

    END_VERSIONS
    """
}
