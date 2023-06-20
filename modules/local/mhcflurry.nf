process MHCFLURRY {
    label 'process_single'
    tag "${metadata.sample}"

    conda "bioconda::mhcflurry=2.0.6"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mhcflurry:2.0.6--pyh7cba7a3_0' :
        'quay.io/biocontainers/mhcflurry:2.0.6--pyh7cba7a3_0' }"

    input:
    tuple val(metadata), path(peptide_file)

    output:
    tuple val(metadata), path("*.tsv"), emit: predicted
    path "versions.yml", emit: versions

    script:

    if (metadata.mhc_class == "II") {
        error("MHCflurry prediction of ${metadata.sample} is not possible with MHC class II!")
    }

    """
    touch mhcflurry_prediction.log

    mhcflurry_prediction.py --input ${peptide_file} --output '${metadata.sample}_predicted_mhcflurry.tsv' --alleles '${metadata.alleles}'

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mhcflurry: \$(mhcflurry-predict --version)
        mhcgnomes: \$(python -c "from mhcgnomes import version; print(version.__version__)")
    END_VERSIONS
    """

    stub:
    """
    mhcflurry_prediction.py --input ${peptide_file} --output '${metadata.sample}_predicted_mhcflurry.tsv' --alleles '${metadata.alleles}'
    touch versions.yml
    """
}
