from memoized import memoized

from custom.inddex.ucr.data_providers.mixins import NutrientIntakesDataMixin


class NutrientIntakesByFoodData(NutrientIntakesDataMixin):
    title = 'Disaggregated Intake Data By Food'
    slug = 'disaggr_intake_data_by_food'
    headers_in_order = [
        'unique_respondent_id', 'location_id', 'respondent_id', 'recall_case_id', 'opened_by_username',
        'owner_name', 'recalled_date', 'recall_status', 'gender', 'age_years', 'age_months', 'age_range',
        'supplements', 'urban_rural', 'pregnant', 'breastfeeding', 'food_code', 'base_term_food_code',
        'reference_food_code', 'caseid', 'food_name', 'recipe_name', 'fao_who_gift_food_group_code',
        'fao_who_gift_food_group_description', 'user_food_group', 'food_type', 'include_in_analysis',
        'is_ingredient', 'food_status', 'total_grams', 'energy_kcal', 'water_g', 'protein_g',
        '<all other nutrients>', 'conv_factor_gap_code', 'conv_factor_gap_desc', 'fct_gap_code', 'fct_gap_desc'
    ]

    def __init__(self, config):
        self.config = config

    @property
    @memoized
    def rows(self):
        return [
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '13017', '19325', '1301199',
             '548ea376-28a1-43e2-8df2-b26ca445d23f', 'Mắm,Nước mắm cá', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '5', '1.7445', '2.56', '0.925', '', '1', 'conversion factor available', '1',
             'fct data available'],
            ['666_1', '', '', '36271593-cb0d-4a99-ac35-260db7d4b63e', 'sue', 'sue', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'peri-urban', 'no', 'no', '7170', '43903', '712499',
             '63069d9d-e46d-4566-b788-b794a2c7f67a', 'Nước luộc,rau', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '299', '0', '15.548', '48.139', '', '1', 'conversion factor available', '2',
             'using fct data from base term food code'],
            ['666_1', '', '', '36271593-cb0d-4a99-ac35-260db7d4b63e', 'sue', 'sue', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'peri-urban', 'no', 'no', '1004002', '32630',
             '100400299', 'ea7ea242-b196-4cfb-8e65-2bfe66b8e199', 'Cơm,tẻ,nấu', '', '', '', '', 'food_item', 'yes',
             '', 'fourth_pass', '147.7136', '', '', '', '', '1', 'conversion factor available', '8',
             'no fct data available'],
            ['555_2', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b14', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '8058', '41969', '805999',
             '126394a1-a907-45fb-9249-663216062664', 'Ruốc,cá', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '61.178', '190.691826', '41.478684', '31.629026', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['666_1', '', '', '36271593-cb0d-4a99-ac35-260db7d4b63e', 'sue', 'sue', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'urban', 'no', 'no', '', '39604', '712499',
             '667c59d9-eebf-4073-be45-9c73950415af', 'Nước luộc,Khác', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '206.74', '0', '10.75048', '33.28514', '', '1', 'conversion factor available', '2',
             'using fct data from base term food code'],
            ['888_1', '', '', 'de16bd5b-51bc-4dac-ba81-50e04ac858e5', 'mary', 'mary', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'rural', 'yes', 'no', '', '10131', '101299',
             '499f034b-95e3-4d02-909d-af382b1cd46e', 'Bánh mỳ,que,không ngọt', '', '', '', '', 'food_item', 'yes',
             '', 'fourth_pass', '250', '', '', '', '', '1', 'conversion factor available', '8',
             'no fct data available'],
            ['8003_1', '', '', '832b98ad-303f-458d-a400-1f8453b358c6', 'mary', 'mary', '2019-08-14', 'Complete',
             'male', '52', '624', '50-64 years', 'no', 'urban', 'no', 'no', '5017', '', '5017',
             '1e1d14d3-a801-4249-ab62-c05f2e92e53b', 'Đu đủ chín', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '', '', '', '', '', '8', 'no conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '8039014', '', '803999',
             'a52b3be8-e445-4705-bfef-73942ae340a2', 'Mực khô,nướng', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '59.9155', '174.2941895', '27.201637', '46.9138365', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['12345_1', '', '', 'fbcc5cd9-3d8c-43c8-908d-abb1c0b21089', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'yes', 'no', '4116', '', '411599',
             '964416e8-6a98-49d4-86df-cd667bad102a', 'Dưa,cải bẹ', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '574.56', '140.19264', '414.25776', '51.13584', '', '1', 'conversion factor available',
             '2', 'using fct data from base term food code'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '5040', '28513', '5040',
             'ac63f5a8-4aec-4551-a843-e7f0b5f10515', 'Ổi', '', '', '', '', 'food_item', 'yes', '', 'fourth_pass',
             '34.2', '', '', '', '', '1', 'conversion factor available', '8', 'no fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '2013002', '48139', '201399',
             '9bfdd247-a9a4-48bd-91a1-3ae83c164a32', 'Khoai sọ,nấu canh', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '123', '149.2359', '83.148', '41.574', '', '1', 'conversion factor available', '1',
             'fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '', '32950', '1200199',
             '075922bb-3837-4b56-88d4-f7f61478e891', 'Bánh quy,Khác', '', '', '', '', 'food_item', 'yes', '',
             'fourth_pass', '10', '37.81', '6.58', '1.74', '', '1', 'conversion factor available', '2',
             'using fct data from base term food code'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '', '44376', '101299',
             '522d98f5-7d58-49dd-96ec-d0ebf6821c06', 'Bánh mỳ,Khác,không ngọt', '', '', '', '', 'food_item', 'yes',
             '', 'fourth_pass', '48', '', '', '', '', '1', 'conversion factor available', '8',
             'no fct data available'],
            ['444567_1', '', '', 'e22a2245-8370-45b5-aea7-f2b8728dbc5e', 'john', 'john', '2019-08-17', 'Complete',
             'male', '22', '264', '15-49 years', 'no', 'urban', 'no', 'no', '5001', '34972', '5001',
             '7bc8b6bc-cc6d-46a2-b552-ca068c3a31d3', 'Bưởi', '', '', '', '', 'food_item', 'yes', '', 'fourth_pass',
             '', '', '', '', '', '8', 'no conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '2013002130250', '10400',
             '2013002130250', '1b3033c5-9ccc-4c92-aa59-13f0d9bb6500', 'Canh khoai sọ', 'Canh khoai sọ', '', '', '',
             'std_recipe', 'no', '', 'fourth_pass', '200', '73.97842', '84.71156', '102.6692', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '2013', '13832', '201399', '',
             'Khoai sọ,sống', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '61.38', '72.98082',
             '22.83336', '7.3656', '', '1', 'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '4082', '25225', '408299', '',
             'Rau mùi tàu,sống', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '0.6', '0.1656',
             '0.0294', '0.3858', '', '1', 'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '4038', '', '403799', '',
             'Hành,lá (hành hoa),sống', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '3.2', '0.832',
             '0.4448', '2.1824', '', '1', 'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '13025', '', '1302599', '',
             'Gia vị mặn,Bột canh', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '0.6', '0', '0.195',
             '0.2418', '', '1', 'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '14018', '', '14018', '', 'Nước', '',
             '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '136.02', '0', '61.209', '92.4936', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '9001008060081', '', '9001008060081',
             '0b77fb58-f265-4897-b817-3a077d81dc3f', 'Trứng gà ta ốp la', 'Trứng gà ta ốp la', '', '', '',
             'std_recipe', 'no', '', 'fourth_pass', '68', '', '', '', '', '1', 'conversion factor available', '8',
             'no fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '6023', '13043', '602399', '',
             'Dầu,Hỗn hợp', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '13.022', '117.198',
             '2.851818', '6.12034', '', '1', 'conversion factor available', '1', 'fct data available'],
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '9001', '31261', '900188', '',
             'Egg,local hen,raw', '', '', '', '', 'food_item', 'yes', 'yes', 'fourth_pass', '70.8968', '', '', '',
             '', '1', 'conversion factor available', '8', 'no fct data available'],
            ['1234_1', '', '', '738d5457-3517-4ef0-b21e-65a7ded2e8d1', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '', '44866', '',
             'cb9c5609-379e-47bb-9cec-349171a4fc20', 'ĐẬU PHỤ RÁN XÀO SẢ ỚT', 'ĐẬU PHỤ RÁN XÀO SẢ ỚT', '', '', '',
             'non_std_recipe', 'no', '', 'fourth_pass', '5.939406', '4.29617034', '3.756404322', '1.098970092', '',
             '2', 'using conversion factor from base term food code', '2',
             'using fct data from base term food code'],
            ['1234_1', '', '', '738d5457-3517-4ef0-b21e-65a7ded2e8d1', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '13039', '', '1300199',
             '005b9946-abe4-411d-bb8f-5dbe3217523c', '(i) Gia vị,Ớt (tươi)', '', '', '', '', 'food_item', 'yes',
             'yes', 'fourth_pass', '0.359964', '0', '0.246935304', '0.273212676', '', '1',
             'conversion factor available', '3', 'using fct data from reference food code'],
            ['1234_1', '', '', '738d5457-3517-4ef0-b21e-65a7ded2e8d1', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '13024', '39369', '1300199',
             '190bf2a1-169d-4344-87d5-57dd3518edc2', '(i) Gia vị,Sả', '', '', '', '', 'food_item', 'yes', 'yes',
             'fourth_pass', '5.579442', '4.29617034', '3.509469018', '0.825757416', '', '1',
             'conversion factor available', '8', 'no fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '', '24167', '',
             '01e36d8e-df92-41e3-a882-250af3c096d8', 'QUẢ SUNG MUỐI', 'QUẢ SUNG MUỐI', '', '', '',
             'non_std_recipe', 'no', '', 'fourth_pass', '', '', '', '', '', '8', 'no conversion factor available',
             '8', 'no fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '', '', '',
             '04b0d499-cbfb-47a0-bb59-299231d6dbc8', '(I) QUẢ SUNY,CẢ VỎ', '', '', '', '', 'non_std_food_item',
             'yes', 'yes', 'fourth_pass', '', '', '', '', '', '8', 'no conversion factor available', '8',
             'no fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '13017', '47625', '1301199',
             'c8d77ab1-5ae0-46ff-ab5a-2843347ffd0f', '(i) Mắm,Nước mắm cá', '', '', '', '', 'food_item', 'yes',
             'yes', 'fourth_pass', '7.5636363636', '2.6389527273', '3.8725818182', '1.3992727273', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '13034', '44216', '13034',
             '6929991b-2a7a-4fc2-b5bf-c74462643000', '(i) Giấm (gạo/bỗng/táo….)', '', '', '', '', 'food_item',
             'yes', 'yes', 'fourth_pass', '2.9381818182', '0', '1.0577454545', '0.4994909091', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '12014', '36162', '1201499',
             'cc39cbf9-4d38-4764-93ee-a6a30b326fea', '(i) Đường,kính', '', '', '', '', 'food_item', 'yes', 'yes',
             'fourth_pass', '9.8909090909', '39.2866909091', '2.5815272727', '1.7605818182', '', '1',
             'conversion factor available', '1', 'fct data available'],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '', '10240', '101799',
             '88fe71d9-fbde-4962-b34c-2ff6918285d3', '(i) Bột,Khác', '', '', '', '', 'food_item', 'yes', 'yes',
             'fourth_pass', '2.9090909091', '10.4843636364', '1.4225454545', '0.4829090909', '', '1',
             'conversion factor available', '2', 'using fct data from base term food code'],
            ['555_2', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b14', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '', '', '',
             '36ce2096-0bda-4c15-a47f-19dc955e76da', 'NƯỚC NGHỆ MẬT ONG', 'NƯỚC NGHỆ MẬT ONG', '', '', '',
             'non_std_recipe', 'no', '', 'fourth_pass', '', '', '', '', '', '8', 'no conversion factor available',
             '8', 'no fct data available'],
            ['555_2', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b14', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '', '', '',
             '9c440036-eb8b-461a-94d8-1afdbebe4e9c', '(I) BỘT NGHỆ,BỘT NGHỆ XAY', '', '', '', '',
             'non_std_food_item', 'yes', 'yes', 'fourth_pass', '', '', '', '', '', '8',
             'no conversion factor available', '8', 'no fct data available'],
            ['555_2', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b14', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '12026', '13343', '12026',
             'a593172b-2c0c-45d5-9533-6ac8cba0b14d', '(i) Mật ong', '', '', '', '', 'food_item', 'yes', 'yes',
             'fourth_pass', '', '', '', '', '', '1', 'conversion factor available', '8', 'no fct data available'],
            ['12345_1', '', '', 'fbcc5cd9-3d8c-43c8-908d-abb1c0b21089', 'mary', 'mary', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'yes', 'no', '', '45831', '',
             '2b4bb306-5fb5-48d8-8c76-8f6be6ae8a9a', 'NƯỚC ĐẬU,NƯỚC ĐẬU TƯƠI THÊM ĐƯỜNG VÀ ĐÁ', '', '', '', '',
             'non_std_food_item', 'yes', '', 'fourth_pass', '', '', '', '', '', '8',
             'no conversion factor available', '8', 'no fct data available'],

        ]


class NutrientIntakesByRespondentData(NutrientIntakesDataMixin):
    title = 'Aggregated Daily Intake By Respondent'
    slug = 'aggr_daily_intake_by_rspndnt'
    headers_in_order = [
        'unique_respondent_id', 'location_id', 'respondent_id', 'recall_case_id', 'opened_by_username',
        'owner_name', 'recalled_date', 'recall_status', 'gender', 'age_years', 'age_months', 'age_range',
        'supplements', 'urban_rural', 'pregnant', 'breastfeeding', 'energy_kcal', 'water_g', 'protein_g',
        '<all other nutrients>'
    ]

    def __init__(self, config):
        super().__init__(config)

    @property
    @memoized
    def rows(self):
        return [
            ['555_1', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b13', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '140.19264', '140.19264',
             '140.19264', ''],
            ['555_2', '', '', 'f3bfc88d-6cb1-4ae8-acdc-9715a9411b14', 'mary', 'mary', '2019-08-12', 'Complete',
             'female', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '140.19264', '140.19264',
             '140.19264', ''],
            ['666_1', '', '', '36271593-cb0d-4a99-ac35-260db7d4b63e', 'sue', 'sue', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'peri-urban', 'no', 'no', '0', '26.29848', '81.42414',
             ''],
            ['888_1', '', '', 'de16bd5b-51bc-4dac-ba81-50e04ac858e5', 'mary', 'mary', '2019-08-14', 'Complete',
             'female', '29', '348', '15-49 years', 'yes', 'rural', 'yes', 'no', '0', '0', '0', ''],
            ['8003_1', '', '', '832b98ad-303f-458d-a400-1f8453b358c6', 'mary', 'mary', '2019-08-14', 'Complete',
             'male', '52', '624', '50-64 years', 'no', 'urban', 'no', 'no', '0', '0', '0', ''],
            ['12345_1', '', '', 'fbcc5cd9-3d8c-43c8-908d-abb1c0b21089', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'yes', 'no', '140.19264', '414.25776', '51.13584',
             ''],
            ['8007_1', '', '', '225281cf-ae7e-4d20-9516-0e64c228467e', 'sue', 'sue', '2019-08-17', 'Complete',
             'female', '1', '14', '6-59 months', 'yes', 'rural', 'no', 'yes', '239.4559072727', '98.6624',
             '47.4562545455', ''],
            ['444567_1', '', '', 'e22a2245-8370-45b5-aea7-f2b8728dbc5e', 'john', 'john', '2019-08-17', 'Complete',
             'male', '22', '264', '15-49 years', 'no', 'urban', 'no', 'no', '0', '0', '0', ''],
            ['1234_1', '', '', '738d5457-3517-4ef0-b21e-65a7ded2e8d1', 'sue', 'sue', '2019-08-17', 'Complete',
             'male', '23', '276', '15-49 years', 'no', 'urban', 'no', 'no', '4.29617034', '3.756404322',
             '1.098970092', ''],
        ]
