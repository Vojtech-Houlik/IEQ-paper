GENERAL INFORMATION

G01. Names of file(s) or dataset(s) that this README file describes:
	- Dataset_ParameterDescription.xlsx
	- FullDataset_CombinedSimple.csv
	- FullDataset_PrimarySchools.csv
	- FullDataset_SecondarySchool.csv
	- FullDataset_TestLectureRoom.csv
	- OccupantSurveys.pdf
G02. Date of creation/last update of the README file: 23/04/2025
G03. Name and contact information of Principal Investigator: Quinten Carton (quinten.carton@kuleuven.be) 
G04. ORCID of Principal Investigator: 0000-0001-7441-2612
G05. Institution of Principal Investigator: KU Leuven
G06. Contact of other person at KU Leuven that has access to the dataset: Hilde Breesch (hilde.breesch@kuleuven.be)
G07. Description of the dataset:
	Contains field measurement data from classrooms in Belgium. These datasets comprise of survey responses, indicating occupants’ satisfaction with the 	indoor environmental quality (IEQ) (i.e., thermal, IAQ, visual, acoustic and overall IEQ conditions), measurements of the indoor environmental 	conditions in the classroom during heating and intermediate season, and contextual variables (e.g., occupant location in classroom). Data was 	collected in three educational case studies: (1) three classrooms in a secondary school (Case 1), seven primary school classrooms (Case 2), and a 	test lecture room at KU Leuven Ghent Campus (Case 3). The full dataset consists of 6834 satisfaction assessments collected from 321 unique occupants 	in classrooms. NOTE: The data in cases 1 and 2 were collected when the COVID-19 regulations were active in classrooms. Consequently, participating 	occupants were obliged to wear face masks which could affect their satisfaction with the IEQ. In addition, it was advised to open at least one 	window in the classroom during occupancy.
G08. Keywords (author defined): occupant satisfaction, IEQ, classroom
G09. Thesaurus or controlled vocabulary keywords: NA
G10. Thesaurus or controlled vocabulary used in this README: NA
G11. Language(s) used in the dataset: English / Dutch
G12. Other involved researchers: 
	- Kolarik, Jakub (Technical University of Denmark) - ORCID: 0000-0002-3872-1802
	- Breesch, Hilde (Associatie KU Leuven) - ORCID: 0000-0001-7088-7231

PROJECT INFORMATION

P01. Project information: 
The data was collected in the frame of Quinten Carton's PhD "Personalised occupant satisfaction models for HVAC control in educational buildings" 

P02. Project abstract:
Providing a good indoor environmental quality (IEQ) in classrooms is important for guaranteeing pupils' and students' satisfaction and learning performance. Occupant-centric control (OCC) for HVAC systems has the potential to improve occupants' satisfaction with the IEQ by including occupants' preferences in the control loop. An OCC system that is responsive to occupants' unique preferences requires a personalised modelling approach for predicting these unique preferences. Currently, personalised comfort models have been defined and tested for predicting thermal comfort preferences. However, these approaches often require a large number of occupant feedback votes, which are challenging to collect in reality. In addition, current modelling approaches are often untransparent which decreases their comprehensibility. Moreover, a personalised modelling approach for predicting occupants' indoor air quality (IAQ) satisfaction has not been defined in literature, limiting the possibilities of defining an OCC system that is responsive to occupants' IAQ preferences. Finally, the application of HVAC control systems integrating personalised comfort models in multi-occupancy spaces (e.g., open-plan offices, classrooms, meeting rooms) is challenging since conflicting occupant preferences have to be resolved. Classrooms in educational buildings is a type of multi-occupancy space that is currently understudied. First, the state-of-the-art on occupant-centric HVAC control systems and personalised comfort models was investigated. Afterwards, three data collection campaigns were conducted in different educational buildings to construct a dataset comprising of occupants' satisfaction and the corresponding IEQ conditions in the classroom. A statistical analysis was performed to determine the main influencing variables for occupants' satisfaction with the IEQ in classrooms. Subsequently, the performance of mixed-effects (ME) models as a personalised modelling approach for predicting occupants' thermal and IAQ satisfaction was evaluated. Finally, an OCC framework was defined which integrates the ME models. The performance of the OCC framework was determined via a simulation study. In total, a dataset comprising of 6834 satisfaction assessments was collected from 321 unique occupants in classrooms. The statistical analyses on the dataset showed that room temperature was significantly associated with occupants' thermal and IAQ satisfaction in all of the monitored classrooms. Other environmental (e.g., CO2-concentration and relative humidity) and contextual variables (e.g., occupants' location in classroom) showed statistically significant relationships with satisfaction, but these were not present in all classrooms. In addition, the results in this project showed that a ME modelling approach was capable of predicting occupants' individual thermal and IAQ preferences. The ME model incorporated the individuality of the occupants and was therefore able to achieve higher prediction accuracies than models that did not take this individuality into account. Moreover, only a limited number of datapoints (i.e., 10 occupant feedback votes) was required to make stable predictions. Simple ME models with room temperature as sole predictor achieved similar accuracies for predicting occupants' thermal and IAQ satisfaction as more complex ME models. Finally, an OCC framework for classrooms, which integrated the ME models, was defined. The OCC framework was able to improve occupants' thermal and IAQ satisfaction.

P03. Project funder: Name of funder, type of grant, grant number

FILE OVERVIEW

F01. Number of files described by the README-file: 6
F02. List with names of files, description, date of creation of file:
	- Dataset_ParameterDescription.xlsx: Description of the parameters included in the four dataset (csv) files.
	- FullDataset_CombinedSimple.csv: Combined dataset from the measurement campaigns in all three cases.
	- FullDataset_PrimarySchools.csv: Detailed dataset from the measurement campaign in case 2.
	- FullDataset_SecondarySchool.csv: Detailed dataset from the measurement campaign in case 1.
	- FullDataset_TestLectureRoom.csv: Detailed dataset from the measurement campaign in case 3.
	- OccupantSurveys.pdf: Overview of the content and structure of the occupant surveys.
F03. File formats: xlsx, csv, pdf
F04. Software used to generate the data: NA
F05. Software necessary to open the file: NA
F06. Relationship between the files: see F02
F07. Which version of the dataset is this? Date of this version?: V1
F08. Information about the dataset versions and reason for updates: NA
F09. Naming conventions for file names: NA

STORAGE INFORMATION

S01. Where are the data stored?: https://doi.org/10.48804/CZQNUU
S02. Links to other available locations of the dataset (e.g. repository): NA

METHODOLOGICAL INFORMATION

M01. Date (beginning-end) and place of data collection: see related publications
M02. Aim for which the data were collected: see related publications
M03. Data collecting method: see related publications
M04. Information about data processing methods: see related publications
M05. Information about the instrument, calibration: see related publications
M06. Quality assurance procedures: see related publications
M07. Information about limitations of the dataset, information that ensures correct interpretation of the dataset: see related publications
M08. People involved in the creation or processing of the dataset: see related publications

DATA ACCESS AND SHARING

A01. Recommended citation for the dataset: 
	@data{CZQNUU_2025,
	author = {Carton, Quinten and Kolarik, Jakub and Breesch, Hilde},
	publisher = {KU Leuven RDR},
	title = {{Data on occupant satisfaction with the indoor environmental quality in classrooms}},
	year = {2025},
	doi = {10.48804/CZQNUU},
	url = {https://doi.org/10.48804/CZQNUU}
	}
A02. License information, restrictions on use: CC-BY-NC-ND-4.0
A03. Confidentiality information: NA

DATA SPECIFIC INFORMATION (ABOUT THE DATA THEMSELVES)

D01. Full names and definitions for columns and rows: see file "Dataset_ParameterDescription.xlsx"
D02. Explanation of abbreviations: see file "Dataset_ParameterDescription.xlsx"
D03. Units of measurement: see file "Dataset_ParameterDescription.xlsx"
D04. Symbols for missing data: NA

RELATIONSHIPS

R01. Publications based on this dataset:
	- Carton, Q., Breesch, H. (sup.), Kolarik, J. (cosup.) (2025). Personalised occupant satisfaction models for HVAC control in educational buildings. 	https://lirias.kuleuven.be/4220268
	- Carton, Q., De Coninck, S., Kolarik, J., Breesch, H. (2023). Assessing the effect of a classroom IEQ on student satisfaction, engagement and 	performance. In: E3S Web of Conferences: vol. 396, (Paper No. 01052). Presented at the The 11th International Conference on Indoor Air Quality, 	Ventilation & Energy Conservation in Buildings (IAQVEC2023), Tokyo, Japan, 20 May 2023-23 May 2023. doi: 10.1051/e3sconf/202339601052 	https://lirias.kuleuven.be/4089111
	- Carton, Q., Mennes, F., Vanden Broeck, S., Van Roy, V., Kolarik, J., Breesch, H. (2023). Evaluation of indoor environmental quality and pupils’ 	satisfaction in Flemish primary schools. In: M. Schweiker, C. van Treeck, D. Müller, J. Fels, T. Kraus, H. Pallubinsky (Eds.), Proceedings of 	Healthy Buildings 2023 Europe, (285-292). Presented at the Healthy Buildings 2023 Europe, Aachen, Germany, 11 Jun 2023-14 Jun 2023. 	https://lirias.kuleuven.be/4097671	
	- Carton, Q., Kolarik, J., Breesch, H. (2022). Driving factors of occupants’ satisfaction with IEQ in a school building. In: Indoor Air 2022 	proceedings, (Paper No. 1297). Presented at the Indoor Air 2022: 17th International Conference of the International Society of Indoor Air Quality & 	Climate, Kuopio, Finland, 12 Jun 2022-16 Jun 2022. https://lirias.kuleuven.be/3791042
R02. This dataset derives from  (other dataset): NA
R03. This dataset is related to  (documents, dataset): NA
R04. References of publications used to create the datasets: NA