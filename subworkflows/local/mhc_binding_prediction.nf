//
// Check input samplesheet and get read channels
//

include { SYFPEITHI } from '../../modules/local/syfpeithi'
include { MHCFLURRY } from '../../modules/local/mhcflurry'
include { MHCNUGGETS } from '../../modules/local/mhcnuggets'
include { NETMHCPAN } from '../../modules/local/netmhcpan'
include { NETMHCIIPAN } from '../../modules/local/netmhciipan'
include { MERGE_PREDICTIONS } from '../../modules/local/merge_predictions'


workflow MHC_BINDING_PREDICTION {
    take:
        metadata_and_file

    main:
        ch_versions = Channel.empty()
        ch_combined_predictions = Channel.empty()

        tools = params.tools?.tokenize(',')

        if (tools.isEmpty()) { exit 1, "No valid tools specified." }

        //correct if tool names are not lowercase
        tools = tools.collect{ it.toLowerCase() }
        //correct if spaces were used
        tools = tools.collect{ it.trim() }

        if ( "syfpeithi" in tools )
        {
        SYFPEITHI ( metadata_and_file )
        ch_versions = ch_versions.mix(SYFPEITHI.out.versions)
        ch_combined_predictions = ch_combined_predictions.join(SYFPEITHI.out.predicted, remainder: true)
        }
        if ( "mhcflurry" in tools )
        {
        MHCFLURRY ( metadata_and_file )
        ch_versions = ch_versions.mix(MHCFLURRY.out.versions)
        ch_combined_predictions = ch_combined_predictions.join(MHCFLURRY.out.predicted, remainder: true)
        }
        if ( "mhcnuggets" in tools )
        {
        MHCNUGGETS ( metadata_and_file )
        ch_versions = ch_versions.mix(MHCNUGGETS.out.versions)
        ch_combined_predictions = ch_combined_predictions.join(MHCNUGGETS.out.predicted, remainder: true)
        }
        if ( "netmhcpan" in tools )
        {
        NETMHCPAN (metadata_and_file)
        ch_versions = ch_versions.mix(NETMHCPAN.out.versions)
        ch_combined_predictions = ch_combined_predictions.join(NETMHCPAN.out.predicted, remainder: true)
        }
        if ( "netmhciipan" in tools )
        {
        NETMHCIIPAN (metadata_and_file)
        ch_versions = ch_versions.mix(NETMHCIIPAN.out.versions)
        ch_combined_predictions = ch_combined_predictions.join(NETMHCIIPAN.out.predicted, remainder: true)
        }

    //remove the null (it[1]) in the channel output
    ch_combined_predictions = ch_combined_predictions.map{ it -> [it[0], it[2..-1]]}
    //join metadata and input channel with metadata and output channel
    ch_combined_predictions = ch_combined_predictions.join(metadata_and_file, remainder: true)

    //merge the prediction output of all tools into one output merged_prediction.tsv
    MERGE_PREDICTIONS (ch_combined_predictions)


    emit: ch_combined_predictions
}
