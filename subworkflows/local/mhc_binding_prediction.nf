//
// Check input samplesheet and get read channels
//

include { SYFPEITHI } from '../../modules/local/syfpeithi'
include { MHCFLURRY } from '../../modules/local/mhcflurry'
include { MHCNUGGETS } from '../../modules/local/mhcnuggets'
include { NETMHCPAN } from '../../modules/local/netmhcpan'
include { NETMHCIIPAN } from '../../modules/local/netmhciipan'

workflow MHC_BINDING_PREDICTION {
    take:
        metadata_and_file

    main:
        ch_versions = Channel.empty()
        tools = params.tools?.tokenize(',')
        if (tools.isEmpty()) { exit 1, "No valid tools specified." }

        if ( "syfpeithi" in tools )
        {
            SYFPEITHI ( metadata_and_file )
            ch_versions = ch_versions.mix(SYFPEITHI.out.versions)
        }
        if ( "mhcflurry" in tools )
        {
        MHCFLURRY ( metadata_and_file )
        ch_versions = ch_versions.mix(MHCFLURRY.out.versions)
        }
        if ( "mhcnuggets" in tools )
        {
        MHCNUGGETS ( metadata_and_file )
        ch_versions = ch_versions.mix(MHCNUGGETS.out.versions)
        }
        if ( "netmhcpan" in tools )
        {
            NETMHCPAN (metadata_and_file)
            ch_versions = ch_versions.mix(NETMHCPAN.out.versions)
        }
        if ( "netmhciipan" in tools )
        {
            NETMHCIIPAN (metadata_and_file)
            ch_versions = ch_versions.mix(NETMHCIIPAN.out.versions)
        }



        // TODO: Combine output
        ch_combined_predictions = SYFPEITHI.out.predicted

    emit: ch_combined_predictions
}
