process NETMHCPAN {
    label 'process_single'
    tag "${meta.id}"

    // conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/de/de9c5fbcc5583f3c096617ef2c8f84c5e69b479cc5a5944f10d0e1d226779662/data' :
        'community.wave.seqera.io/library/bash_gawk_perl_tcsh:a941b4e9bd4b8805' }"

    input:
    tuple val(meta), val(alleles_input), path(tsv), path(software)

    output:
    tuple val(meta), path("*.xls"), emit: predicted
    path "versions.yml", emit: versions

    script:
    if (meta.mhc_class != "I") {
        error "NETMHCPAN only supports MHC class I. Use NETMHCIIPAN for MHC class II."
    }
    def args    = task.ext.args ?: ''
    def prefix  = task.ext.prefix ?: "${meta.id}"
    def alleles = alleles_input

    """
    # netMHCpan formats the software directory (NMHOME, derived from the wrapper's own path) and
    # TMPDIR into fixed-size C buffers and aborts with "buffer overflow detected" / "stack smashing
    # detected" once they get too long (~95 chars for netMHCpan-4.2b, ~200 for netMHCIIpan-4.3).
    # The staged `netmhcpan/` dir lives inside the Nextflow work dir, whose path easily exceeds that,
    # so call the wrapper through a short symlink under /tmp (deliberately not \$TMPDIR, which
    # may itself be long) and point TMPDIR there too. The symlink dir is removed on exit.
    nm=\$(mktemp -d /tmp/nm.XXXXXX)
    trap 'rm -rf "\$nm"' EXIT
    ln -s "\$PWD/netmhcpan" "\$nm/netmhcpan"
    export TMPDIR="\$nm"

    "\$nm/netmhcpan/netMHCpan" \
        -p $tsv \
        -a $alleles \
        -xls \
        -xlsfile ${prefix}_predicted_netmhcpan.xls \
        $args

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        \$(cat netmhcpan/data/version | sed -s 's/ version/:/g')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}_predicted_netmhcpan.xls

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        \$(cat netmhcpan/data/version | sed -s 's/ version/:/g')
    END_VERSIONS
    """
}
