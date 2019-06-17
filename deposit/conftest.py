import pytest

from backend.conftest import load_test_data as papers_load_test_data

from deposit.models import License

load_test_data = papers_load_test_data

@pytest.fixture()
def license_standard(db):
    """
    Returns a standard test license
    """

    license = License.objects.get_or_create(
        name="Standard License",
        uri="https://dissem.in/deposit/license/standard"
    )

    return license

@pytest.fixture()
def license_alternative(db):
    """
    Returns an alternative test license
    Use this license, if you need two of them
    """

    license = License.objects.get_or_create(
        name="Alternative License",
        uri="https://dissem.in/deposit/license/alternative"
    )

    return license


# This is a list of oairecords to be tested
metadata_publications = [
    'book-chapter_acute_interstitial_nephritis',
    'book-chapter_adaptive_multiagent_system_for_multisensor_maritime_surveillance',
    'book_god_of_the_labyrinth',
    'dataset_sexuality_assessment_in_older_adults_unique_situations',
    'journal-article_a_female_signal_reflects_mhc_genotype_in_a_social_primate',
    'journal-article_altes_und_neues_zum_strafrechtlichen_vorsatzbegriff',
    'journal-article_confrontation_with_heidegger',
    'journal-article_constructing_matrix_geometric_means',
    'journal-article_lobjet_de_la_dpression',
    'other_assisting_configuration_based_feature_model_composition',
    'proceedings-article_activitycentric_support_for_weaklystructured_business_processes',
    'proceedings-article_an_efficient_vofbased_rans_method_to_capture_complex_sea_states',
    'reference-entry_chromatin_interaction_analysis_using_pairedend_tag_sequencing',
]


@pytest.fixture(params=metadata_publications)
def publication(request, load_json):
    """
    Loads the above list of OaiRecords and corresponding Papers one after the other and returns the Paper object
    """
    return load_json.load_oairecord(request.param)[0]
