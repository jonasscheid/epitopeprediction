//
// Check input samplesheet and get read channels
//

include { SAMPLESHEET_CHECK } from '../../modules/local/samplesheet_check'

workflow INPUT_CHECK {
    take:
    samplesheet // file: /path/to/samplesheet.csv

    main:
    SAMPLESHEET_CHECK ( samplesheet )
        .tsv
        .splitCsv ( header:true, sep:'\t' )
        .map { get_samplesheet_paths(it) }
        .set { metadata_and_files }

    emit: metadata_and_files                  // channel: [ val(metadata), [ files ] ]
    versions = SAMPLESHEET_CHECK.out.versions // channel: [ versions.yml ]
}


def get_samplesheet_paths(LinkedHashMap row) {
    //---------
    // Save sample, alleles, mhc_class and file_type in a dictionary (metadata)
    // and return a list of meta and the filename.
    //---------
    def metadata = [:]
    metadata.sample         = row.sample
    metadata.alleles        = row.alleles
    metadata.mhc_class      = row.mhc_class
    metadata.file_type      = row.file_type

    return [ metadata, file(row.filename) ]
}
