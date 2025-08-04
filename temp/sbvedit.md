<!--
meta-appversion: 16.0000
meta-author: Ana Angelovska
meta-changed: 2025-08-01T12:19:00
meta-changedby: Andres Cevallos
meta-content-type: text/html; charset=utf-8
meta-created: 2025-06-05T07:20:00
meta-generator: LibreOffice 7.4.7.2 (Linux)
-->

# Study Info

 **Client**: Silicon Valley Bank

 **Country**: United States of America

 **Stakeholder**: Innovators

 **Type**: Targeted Stakeholder

 **Methodology**: Online

# GENERAL REQUIREMENTS

 **PROGRAMMER:**

- Throughout the questionnaire please use the pre\-codes and question numbers specified. Do not show codes unless specified.
- Each question to be asked of ALL unless otherwise specified.
- Each question (including intro questions) should be shown on their own screen unless specified. If this is not clear please verify.
- For each question, include the scale at the top and bottom of the grid.
- Remove navigation drop down box and back button when ready to go live.
- Always anchor Other, None and Don’t know answer options unless otherwise specified.
- Always program None and Don't know answer options as mutually exclusive unless otherwise specified.
- Add HIDDEN Variables:

    - **\[Month] Month of Interview \[hidden]**
    - **\[Day] Day of week (1\-7\) of interview \[hidden] \[1\=Sunday … 7\=Saturday]**
    - **\[Start] Start time of interview \[hidden]**
    - **\[End] End time of interview \[hidden]**
    - **\[Duration] time it took to complete interview; format “minutes” \[hidden]**
- Please include all HIDDEN variables in all SPSS deliverable files.
- Please include question instruction text from codebook.
- Deliver: SPSS RDG, Soft Launch, and Final data file (final data files all touches unstacked, completes stacked file)
- Provide a reportal link or an updated excel sheet (every day) at the start of data collection with the following variables:

    - **\[Age]**
    - **\[Gender]**
    - **\[Region]**
    - **\[Rating]**

 **Objective:**

- **To program all sections of the questionnaire so that while in field we can efficiently turn “on” and “off” any section on a company level**

 **Project Management**:

 Primary Contact Person: James Schortemeyer ([jschortemeyer@reptrak.com](mailto:jschortemeyer@reptrak.com))

# Programming Notes

 **Languages:**

| **Variable Code** | **Language** |
| 1000 | English |

**Country code:**

| **Country** | **Country Code** |
| United States of America | 27 |

# HARD QUOTAS

**Age by Gender Hard Quotas (\+/\- 1%)**

See corresponding codebook for each country

# SOFT QUOTAS

**Regional Soft Quotas (\+/\-5%)**

See corresponding codebook for each country

# Section 1000 \- Study Intro Text

 **Section1000\_Intro \[SCREENER]**: The RepTrak Company is conducting a study to understand your opinions about some large companies that you may know. The questions will cover the companies’ products and services, social responsibility and financial performance, as well as a number of other topics.

 We are interested in your responses even if they are only based on your overall impressions of these companies.

 This survey will take approximately 10\-15 minutes to complete.

 \=\=\=

 \*\*\*

# Section 2000 \- Demographics

 **Q2000\_Intro \[SCREENER]**: To start, we would like to ask you some initial questions used to divide respondents into groups, which later can be compared. Your answers will not be used to identify you personally; rather they will be used to look for more general tendencies.

 \=\=\=

 \*\*\*

 **Gender**: What is your gender?

 \=\=\=

- **SINGLE** **ANSWER**

 **VARIABLES TABLE**

| **Value** **Code** | **Value** **Label** |
| 1 | Male |
| 2 | Female |

 \*\*\*

 **AGE\_ORI \[AGE\_STANDARD]**:What is your age as of today?

 \=\=\=

- **Programmer:** **Numeric open ended**
- **Programmer: Valid** **Range “0\-115”**

 **Terminate:** **if AGE\_ORI is below 21**

 \*\*\*

 **Region\_C\[GEOGRAPHIC\_AREA\_REGION]:**

 **(US ONLY:)** Which state do you live in?

 **(ALL OTHER NON\-US COUNTRIES:)** Which region do you live in?

 \=\=\=

- **SINGLE ANSWER**
- **Show drop down list – order in alpha\-ascending (anchoring “Other”)**
- **See corresponding codebook for each country**

    - **If Country is US (Code\=27\), then** **Terminate** **if selected any state considered as “Non\-Continental US” within codebook**

Region \[HIDDEN – “Region” is recoded from “Region\_C]:

- **See corresponding codebook for each country**

 \*\*\*

 **Q\_L\_8023\_008\_1:** How closely would you say your life is tied to the innovation economy?

 (Examples of being involved in the innovation economy include: Investing for personal and/or business reasons; Being employed by innovative companies in technology, health care, and/or life sciences industries; Being highly engaged with innovative companies in technology, health care, and/or life sciences industries)

 \=\=\=

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | Not close at all 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | Somewhat close 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | Very closely tied 7 |
| 99 | Not sure |

 **INNOVATORS \[AUTOFILL]:**

| 1 | Yes | **if** **\_L\_8023\_008\_1 \= 5\-7** |
| 2 | No | **if** **\_L\_8023\_008\_1 \= 1\-4; 99** **\[TERMINATE]** |

 \*\*\*

# Section 100 – Familiarity (Screener)

 **S105 \[S105\_RATING\_FAMILIARITY]**: How familiar are you with the following companies?

 \=\=\=

- **SINGLE ANSWER FOR EACH COMPANY**
- **randomize list**
- **\[PN: The number of companies surveyed each month will vary] \[PN: All companies will be surveyed each month] \[PN: In all countries where there are 20\+ companies, please show no more than 20 per page – A respondent will only see 20 even if the company list is longer. If the respondent does not pass the familiarity test for the first 20 companies, please show a second set of 20 companies]**
- **See RepTrak Codebook for Company Codes and List for fielding**

| 1 | Company x |
| 2 | Company x |
| 3 | Company x |
| 4 | Company x |
| 5 | Company x |
| 6 | Company x |
| 7 | Company x |
| 8 | Company x |
| 9 | Company x |
| 10 | Company x |
| 11 | Company x |
| 12 | Company x |
| 13 | Company x |
| 14 | Company x |
| 15 | Company x |
| 16 | Company x |
| 17 | Company x |
| 18 | Company x |
| 19 | Company x |
| 20 | Company x |

 **COLUMNS TABLE**

| **Variable Code** | **Variable Label** | **Notes** |
| 1 | Not at all familiar 1 | Terminate |
| 2 | 2 | Terminate |
| 3 | Have only heard the name 3 | Terminate |
| 4 | 4 |  |
| 5 | Somewhat familiar 5 |  |
| 6 | 6 |  |
| 7 | Very familiar 7 |  |
| 99 | Not sure | Terminate |

- **PN: A respondent must answer 4, 5, 6, or 7 for at least one company in S105 to continue, otherwise****Terminate**

 **Qualified Companies \[HIDDEN]: Select those companies that the respondent selected 4, 5, 6, or 7 in S105**

| **Variable Code** | **Variable Label** |
| 1 |  |
| 2 |  |
| 3 |  |
| 4 |  |
| 5 |  |

- **RANDOMLY select 2 companies from the qualified companies which have not met their rating quota**

 **Industry \[HIDDEN Variable]:**

- **Programmer:** **RepTrak** **will provide in Codebook for each company their industry, this variable will be used for Q360/Q361/Q362\. Please add it to the Data file.**

 **Company\_Type \[HIDDEN Variable]:**

- **Programmer:** **RepTrak** **will provide in Codebook for each company their “type” (Client, Benchmark). Please add it to the Data file.**

 **\[PN: Below flagging is to be done in all countries]**

 **PassedFam\_Count** **\[HIDDEN Variable]:**

- **Programmer: If respondent selects punch 4\-7 at S105 for ALL companies shown then flag with a “1”.**

 **DummyCompany\_Count** **\[HIDDEN Variable]:**

- **Programmer: We will be including 2 Dummy companies at all times at S105 (list of 20 real companies and a list of 2 fake companies)**
- **The dummy companies are:**

1. **Crooked Smile Dental Associates**
2. **Pitbull and Poodle Partners**
3. **Crash Course Trucking Company**
4. **Itchy's Clothing and Apparel**
5. **Expired Food Distributors (EFD)**
6. **Estimating Accountant Group**
7. **Tangled Wireless**
8. **Misdirection Navigators GPS**
9. **Splinter's Lumber**

- **For each country, please select randomly 2 dummy companies among the list here above**
- **If a respondent selects 4\-7 for 1 of the dummy companies then flag them “1”.**
- **If a respondent selects 4\-7 for both of the dummy companies, then flag them “2”.**
- **If respondent is only familiar with two dummy companies and no others then they will be** **terminated**
- **\[PN: Never select a dummy company to be rated]**

 \*\*\*

# Section 305 – Pulse (Company1, Company2, company3\)

 **Q305\_Intro****\[SCREENER]**: You have been randomly assigned to rate **\<b\>{\#Company1}\</b\>** on a variety of characteristics. Even if you do not believe you have enough information to rate this company, please share your impression of the company based on anything you might know or might have read, seen or heard.

 \=\=\=

- **PN: if respondent qualifies to rate Company 2, use variable naming “Q306\_Intro”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q307\_Intro”**

 \*\*\*

 **Q305\[PULSE\_FILTER]**: We would now like you to evaluate **\<b\>{\#Company1}\</b\>** on a variety of characteristics.

 Please consider the following statements and select a number from “1” to “7” where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 For each statement we have provided a “Not Sure” option. Please answer “Not Sure” only if you have absolutely no opinion about this particular statement.

 \=\=\=

- **SINGLE ANSWER FOR EACH ITEM**
- **randomize list**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q306”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q307”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** |
| Q305\_1 | **\<b\>{\#Company1}\</b\>** has a good overall reputation |
| Q305\_2 | **\<b\>{\#Company1}\</b\>** is a company I have a good feeling about |
| Q305\_3 | **\<b\>{\#Company1}\</b\>** is a company that I trust |
| Q305\_4 | **\<b\>{\#Company1}\</b\>** is a company that I admire and respect |

- **Programmer: Show scale numbers, except on “Not sure”**

 **COLUMNS TABLE**

| **Value** **Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

- **Programmer:**
- Respondent must answer at least 3 of 4 statements in Q305 with punch 1\-7 to continue rating **Company1**

    - Rated\_305 \[HIDDEN] \= Rated
- If respondent does **not** answer at least 3 of 4 statements in Q305 with punch 1\-7 and is **eligible** to rate an additional company go to **Section 306**

    - Rated\_305 \[HIDDEN] \= Not Rated
- If respondent does **not** answer at least 3 of 4 statements in Q305 with punch 1\-7 and is **not** **eligible** to rate an additional company **Terminate**

 <img src='sbvedit_html_eb7d90a0278ab058.gif' alt='Shape1' title='' width='678' height='212' />  - **Programmer:**
- Respondent must answer at least 3 of 4 statements in Q305 with punch 1\-7 to continue rating **Company1 \[SAME LOGIC FOR Company2 and Company3]**

    - Rated\_305 \[HIDDEN] \= Rated
- If respondent does **not** answer at least 3 of 4 statements in Q305 with punch 1\-7 and is **eligible** to rate an additional company go to **Section 306**

    - Rated\_305 \[HIDDEN] \= Not Rated
- If respondent does **not** answer at least 3 of 4 statements in Q305 and Q306 with punch 1\-7 and is **eligible** to rate an additional company go to **Section 307**

    - Rated\_306 \[HIDDEN] \= Not Rated
- If respondent does **not** answer at least 3 of 4 statements in Q305 and Q306 and Q307 with punch 1\-7 and is **not** **eligible** to rate an additional company **Terminate**

 **LOGIC FOR THE POSSIBLITY OF A THIRD LOOP. DO NOT IMPLEMENT 3****RD** **LOOP.**

 **Rated\_305 \[HIDDEN]**:

| **Value Code** | **Value Label** |
| 1 | Rated |
| 2 | Not rated |

 \*\*\*

# Section 320 – Attributes (Company1, Company2, company3\)

 **Q320\_Intro****\[SCREENER]**: We would like you to examine some specific statements, and indicate how well you think they describe **\<b\>{\#Company1}\</b\>**.

 For each statement we have provided a “Not Sure” option. Please answer “Not Sure” only if you have absolutely no opinion about this particular statement. We are interested in your personal view, so please answer based on your own perceptions of **\<b\>{\#Company1}\</b\>** and not based on how you think others might perceive it.

 \=\=\=

- **PN: if respondent qualifies to rate Company 2, use variable naming “Q321\_Intro”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q322\_Intro”**

 \*\*\*

 **Q320**: Please select a number from “1” to “7” where “1” means “Does not describe well” and “7” means “Describes very well”.

 **\<b\>{\#Company1}\</b\>**:

 \=\=\=

- **SINGLE ANSWER FOR EACH ITEM**
- **randomize list**
- **SPLIT LIST EVENLY ACROSS TWO PAGES**
- **PLEASE DISPLAY SCALE RESPONSE (Does not describe well 1, 2, …, Not sure) ALSO AT THE BOTTOM OF THE GRID**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q321”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q322”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Dimension** |
| Q320\_1 | Offers high quality products and services | Products \& Services |
| Q320\_2 | Offers products and services that are a good value for the money | Products \& Services |
| Q320\_3 | Stands behind its products and services | Products \& Services |
| Q320\_4 | Meets customer needs | Products \& Services |
| Q320\_5 | Is an innovative company | Innovation |
| Q320\_6 | Is generally the first company to go to market with new products and services | Innovation |
| Q320\_7 | Adapts quickly to change | Innovation |
| Q320\_8 | Offers equal opportunities in the workplace | Workplace |
| Q320\_9 | Rewards its employees fairly | Workplace |
| Q320\_10 | Demonstrates concern for the health and well\-being of its employees | Workplace |
| Q320\_11 | Is fair in the way it does business | Governance |
| Q320\_12 | Behaves ethically | Governance |
| Q320\_13 | Is open and transparent about the way the company operates | Governance |
| Q320\_14 | Acts responsibly to protect the environment | Citizenship |
| Q320\_15 | Has a positive influence on society | Citizenship |
| Q320\_16 | Supports good causes | Citizenship |
| Q320\_17 | Is a well\-organized company | Leadership |
| Q320\_18 | Has a strong and appealing leader | Leadership |
| Q320\_19 | Has excellent managers | Leadership |
| Q320\_20 | Has a clear vision for its future | Leadership |
| Q320\_21 | Is a profitable company | Performance |
| Q320\_22 | Shows strong prospects for future growth | Performance |
| Q320\_23 | Delivers financial results that are better than expected | Performance |
| Q320\_24 | Has strong data privacy and security practices | TEST 1 |
| Q320\_999 | For quality purposes, please select “2” for this row | Terminate if do not select “2” |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | Does not describe well 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | Describes very well 7 |
| 99 | Not sure |

 **\[PN: No coding required for internal labels in “Dimension” column]**

 \*\*\*

# Section 215 – Supportive Behavior (Company1, Company2, company3\)

 **Q215**: The next questions concern a number of different attitudes or behaviors you might have toward a company.

 Please consider how well they describe your attitude toward **\<b\>{\#Company1}\</b\>**.

 Please select a number from 1 to 7 where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 \=\=\=

- **SINGLE ANSWER EACH ITEM.**
- **RANDOMIZE.**
- **PLEASE DISPLAY SCALE RESPONSE (I strongly agree 1, 2, …, Not sure) ALSO AT THE BOTTOM OF THE GRID**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q216”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q217”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **NOTES** |
| Q215\_3 | I would say something positive about **\<b\>{\#Company1}\</b\>** |  |
| Q215\_4 | I would give the benefit of the doubt to **\<b\>{\#Company1}\</b\>** if the company was facing a crisis |  |
| Q215\_5 | If **\<b\>{\#Company1}\</b\>** was faced with a product or service problem, I would trust them to do the right thing |  |
| Q215\_6 | If I had the opportunity, I would buy the products/services of **\<b\>{\#Company1}\</b\>** |  |
| Q215\_7 | If I had the opportunity, I would invest in **\<b\>{\#Company1}\</b\>** |  |
| Q215\_8 | If I had the opportunity, I would work for **\<b\>{\#Company1}\</b\>** |  |
| Q215\_10 | I would recommend the products/services of **\<b\>{\#Company1}\</b\>** |  |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

 \*\*\*

# Section 410 – Expressiveness Battery (Company1, Company2, company3\)

 **Q410\_Intro****\[SCREENER]****:**The next questions ask about the actions of **\<b\>{\#Company1}\</b\>**. Again, please consider how well they reflect your opinions.

 \=\=\=

- **PN: if respondent qualifies to rate Company 2, use variable naming “Q411\_Intro”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q412\_Intro”**

 \*\*\*

 **Q410****:** Please select a number from “1” to “7” where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 \=\=\=

- **SINGLE ANSWER EACH ITEM.**
- **RANDOMIZE.**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q411”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q412”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Internal Notes** |
| Q410\_1 | **\<b\>{\#Company1}\</b\>** communicates often |  |
| Q410\_2 | **\<b\>{\#Company1}\</b\>** stands out from the crowd | Brand Strength Attribute |
| Q410\_3 | **\<b\>{\#Company1}\</b\>** delivers a consistent experience | Brand Strength Attribute |
| Q410\_5 | **\<b\>{\#Company1}\</b\>** appears genuine about what it says and what it stands for | Brand Strength Attribute |
| Q410\_6 | **\<b\>{\#Company1}\</b\>** welcomes open discussion with outside audiences about its activities |  |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

\*\*\*

# Section 420 – Personality Battery (Company1, Company2, company3\)

 **Q420****:**Next, we would like you to think about **\<b\>{\#Company1}\</b\>** as if it were a person. Please select any of the following which you associate with **\<b\>{\#Company1}\</b\>**.

 \=\=\=

- **MULTICODE OK.**
- **RANDOMIZE.**
- **SPLIT ACROSS 2 COLUMNS.**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q421”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q422”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Comments** |
| Q420\_17 | Hard\-working |  |
| Q420\_18 | Intelligent |  |
| Q420\_19 | Confident |  |
| Q420\_20 | Exciting |  |
| Q420\_21 | Modern |  |
| Q420\_22 | Friendly |  |
| Q420\_27 | Creative |  |
| Q420\_28 | Caring |  |
| Q420\_30 | Tech\-savvy |  |
| Q420\_37 | Traditional |  |
| Q420\_38 | Progressive |  |
| Q420\_40 | Greedy |  |
| Q420\_42 | Lazy |  |
| Q420\_43 | Boring |  |
| Q420\_44 | Environmentally\-conscious |  |
| Q420\_45 | Aggressive |  |
| Q420\_99 | None of the above | **\[Anchor, Exclusive]** |

 \*\*\*

# Section 600 – Touch Points (Company1, Company2, company3\)

 **Q600A****:** In the last 12 months, have you used or purchased any products and services from **\<b\>{\#Company1}\</b\>**?

 \=\=\=

- **SINGLE ANSWER**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q601A”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q602A”**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | Yes |
| 0 | No |

\*\*\*

 **Q600****:** In the last 3 months, have you read, seen, or heard information about **\<b\>{\#Company1}\</b\>** through:

 \=\=\=

- **MULTICODE OK.**
- **randomize list**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q601”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q602”**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** | **Notes** |
| Q600\_19 | **\<b\>{\#Company1}\</b\>** advertisements on television, radio or print media |  |
| Q600\_20 | **\<b\>{\#Company1}\</b\>** advertisements on online channels (social media channels like Twitter, Facebook, LinkedIn, Instagram, YouTube, websites, etc.) |  |
| Q600\_4 | **\<b\>{\#Company1}\</b\>’s** website/app |  |
| Q600\_6 | Emails, brochures, direct mail from **\<b\>{\#Company1}\</b\>** |  |
| Q600\_21 | News or information through TV, radio, print, online channels like news websites about **\<b\>{\#Company1}\</b\>** |  |
| Q600\_10 | News or information through social media channels (e.g., Twitter, Facebook, LinkedIn, Instagram, YouTube) about **\<b\>{\#Company1}\</b\>** from other people |  |
| Q600\_14 | Word of mouth (from family members, friends, or colleagues) |  |
| Q600\_22 | Influencers (i.e., topic experts, analysts, bloggers) |  |
| Q600\_16 | **\<b\>{\#Company1}\</b\>****’s** customer support service or employees |  |
| Q600\_18 | News or information on **\<b\>{\#Company1}\</b\>****’s** own social media accounts (e.g.,Twitter, Facebook, LinkedIn, Instagram, YouTube…) |  |
| Q600\_33 | Reviews about **\<b\>{\#Company1}\</b\>****’s** products or services |  |
| Q600\_34 | **\<b\>{\#Company1}\</b\>** advertisements on billboards, airports, buses |  |
| Q600\_99 | None of the above | **ANCHOR.EXCLUSIVE** |

\*\*\*

 **\[ASK Q605 only if any answer from Q600\_19 to Q600\_35 is selected (Q600\_99 is not selected)]**

**Q605****:** You mentioned in the last 3 months, you have read, seen, or heard information about **\<b\>{\#Company1}\</b\>**.

Following that, in which of the following ways have you engaged with **\<b\>{\#Company1}\</b\>**?

 \=\=\=

- **MULTICODE OK.**
- **Randomize list**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q606”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q607”**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** | **Internal Notes** |
| Q605\_1 | Search for information, reviews on **\<b\>{\#Company1}\</b\>** or its products and services online |  |
| Q605\_2 | Use or purchase a product or a service of **\<b\>{\#Company1}\</b\>** |  |
| Q605\_3 | Click on/engage with an advertisement, post, video on online platforms (social media channels such as Twitter, Facebook, LinkedIn, Instagram, YouTube, search engines like Google, news websites or other) about **\<b\>{\#Company1}\</b\>** |  |
| Q605\_4 | Reshare or post content about **\<b\>{\#Company1}\</b\>** online |  |
| Q605\_5 | Reach out to **\<b\>{\#Company1}\</b\>** (for inquiries, comments, etc.) |  |
| Q605\_6 | I have not taken any action | **ANCHOR.EXCLUSIVE** |
| Q605\_99 | None of the above | **ANCHOR.EXCLUSIVE** |

\*\*\*

# Section 800 – CSR (Company1, Company2, Company3\)

 **Q800****:** The next questions ask about the societal relevance of **\<b\>{\#Company1}\</b\>.** Again, please consider how well they reflect your opinions. Please select a number from “1” to “7” where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 \=\=\=

- **SINGLE ANSWER EACH ONE.**
- **RANDOMIZE.**
- **PN: if respondent qualifies to rate Company 2, use variable naming “Q801”**
- **PN: if respondent qualifies to rate Company 3, use variable naming “Q802”**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Internal Notes** |
| Q800\_2 | **\<b\>{\#Company1}\</b\>** improves people’s lives through its social actions | Societal Impact Attribute |
| Q800\_3 | **\<b\>{\#Company1}\</b\>** improves people’s lives through its products and services | Societal Impact Attribute |
| Q800\_4 | **\<b\>{\#Company1}\</b\>** manages its supply chain responsibly (treats suppliers fairly, fights child labor and abusive labor conditions) | Responsible management of the value chain Attribute |
| Q800\_5 | **\<b\>{\#Company1}\</b\>** manages energy efficiently and is a responsible user of natural resources | Responsible management of the value chain Attribute |
| Q800\_6 | **\<b\>{\#Company1}\</b\>** helps improve and support local communities where it operates | Improving the Business Environment Attribute |
| Q800\_7 | **\<b\>{\#Company1}\</b\>** has a positive economic contribution to society (through taxes and job creation where it operates) | Improving the Business Environment Attribute |
| Q800\_8 | **\<b\>{\#Company1}\</b\>** has a clear purpose beyond economic benefits, such as environmental impact | Redesigning the Business Model |
| Q800\_9 | **\<b\>{\#Company1}\</b\>** actively works to reduce its environmental footprint | Redesigning the Business Model |
| Q800\_50 | **\<b\>{\#Company1}\</b\>** has a diverse leadership and invests in diversity, equity and inclusion (DEI) | ESG Testing |
| Q800\_51 | **\<b\>{\#Company1}\</b\>** is ethical in its advertising, product labeling and communications | ESG Testing |
| Q800\_52 | **\<b\>{\#Company1}\</b\>** invests responsibly by considering environmental and social impacts | ESG Testing |
| Q800\_53 | **\<b\>{\#Company1}\</b\>** is taking action to fight climate change | ESG Testing |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

 **\[PN: No coding required for “internal notes” labels]**

\*\*\*

# ADDITIONAL QUESTIONS

 **\[ASK OF ALL WHO RATED SILICON VALLEY BANK** **USA****]**

 **Q\_NY\_8023\_014\_1\[YES\_NO]****:** Do you recall seeing advertisements from Silicon Valley Bank (SVB) this year??

 \=\=\=

- **SINGLE ANSWER**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | Yes |
| 0 | No |
| 99 | Not sure |

 \*\*\*

 **Q\_N\_8023\_010:.** In your opinion, please select the statements that describe Silicon Valley Bank from the following list.

 Silicon Valley Bank can contribute to the success of…

 Select all that apply.

 \=\=\=

- **randomize list**
- **multi\-select**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** |
| Q\_N\_8023\_010\_1 | Start\-up companies |
| Q\_N\_8023\_010\_2 | Companies looking for an exit (i.e., IPO or acquisition) |
| Q\_N\_8023\_010\_3 | Venture Capital (VC) firms |
| Q\_N\_8023\_010\_4 | Private Equity (PE) firms |
| Q\_N\_8023\_010\_5 | Limited Partners (LPs) |
| Q\_N\_8023\_010\_6 | My personal wealth |

 \*\*\*

 **Q\_L\_8023\_15****:** How strongly do you agree or disagree with the following statements about Silicon Valley Bank?

Sillicon Valley Bank (SVB) is…

Please select a number from “1” to “7” where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 \=\=\=

- **SINGLE ANSWER EACH ONE.**
- **RANDOMIZE.**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Internal Notes** |
| Q\_L\_8023\_15\_1 | **Competent** – has banking/finance expertise |  |
| Q\_L\_8023\_15\_2 | **Accountable** – takes responsibility for what it does and says |  |
| Q\_L\_8023\_15\_3 | **Consistent** – can be relied upon to behave and perform in a similar way over time |  |
| Q\_L\_8023\_15\_4 | **Dependable** – is available, reliable, and able to predict and meet your needs |  |
| Q\_L\_8023\_15\_5 | **Transparent** – makes every effort to share information based on accurate verifiable facts |  |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

**\[PN: No coding required for “internal notes” labels]**

 \*\*\*

 **Q\_L\_8023\_16:** Silicon Valley Bank was acquired by First Citizens Bank in March 2023\.

 How strongly do you agree or disagree with the following statements about First Citizens Bank?

 First Citizens Bank is…

Please select a number from “1” to “7” where “1” means “I strongly disagree” and “7” means “I strongly agree”.

 \=\=\=

- **SINGLE ANSWER EACH ONE.**
- **RANDOMIZE.**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** | **Internal Notes** |
| Q\_L\_8023\_16\_1 | **Competent** – has banking/finance expertise |  |
| Q\_L\_8023\_16\_2 | **Accountable** – takes responsibility for what it does and says |  |
| Q\_L\_8023\_16\_3 | **Consistent** – can be relied upon to behave and perform in a similar way over time |  |
| Q\_L\_8023\_16\_4 | **Dependable** – is available, reliable, and able to predict and meet your needs |  |
| Q\_L\_8023\_16\_5 | **Transparent** – makes every effort to share information based on accurate verifiable facts |  |

 **COLUMNS TABLE**

| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | I strongly agree 7 |
| 99 | Not sure |

**\[PN: No coding required for “internal notes” labels]**

 \*\*\*

 **Q\_L\_8023\_011:** How strongly do you agree or disagree with the following statements about Silicon Valley Bank?

 \=\=\=

- **SINGLE ANSWER PER ITEM**

- **RANDOMIZE**

 **VARIABLES TABLE**

| **Variable Name** | **Variable Label** |
| Q\_L\_8023\_011\_2 | Silicon Valley Bank meets the evolving needs of companies, firms, and/or individuals in the innovation economy |
| Q\_L\_8023\_011\_3 | Silicon Valley Bank builds long\-term relationships with clients |
| Q\_L\_8023\_011\_4 | Silicon Valley Bank has deep expertise in technology, healthcare, and life sciences industries |
| Q\_L\_8023\_011\_5 | Silicon Valley Bank can help me tap into experts and valuable insights in the innovation economy |
| Q\_L\_8023\_011\_6 | Silicon Valley Bank is a bank that I trust |

 **COLUMNS TABLE**

| **Variable Code** | **Variable Label** |
| 1 | Strongly disagree 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | Neither agree nor disagree 4 |
| 5 | 5 |
| 6 | 6 |
| 7 | Strongly agree 7 |
| 99 | Not sure |

 \*\*\*

# Section 3000 – Demographics

 **\[ASK ALL]**

 **Q3000\_Intro****\[SCREENER]****:** Finally, we would like you to answer some additional background questions.

 \=\=\=

 \*\*\*

 **ONLY ASK HISPANIC IF COUNTRY\=UNITED STATES (CODE\=27\)**

 **HISPANIC****:**Are you of Hispanic origin, such as Latin American, Mexican, Puerto Rican, or Cuban?

 \=\=\=

- **Programmer: US only (Country Code \= 27\)**
- **SINGLE ANSWER**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | Yes |
| 0 | No |
| 99 | Prefer not to answer |

 \*\*\*

 **ONLY ASK RACE:**

- **IF COUNTRY\=UNITED STATES (CODE\=27\)**

 **RACE****:** Do you consider yourself:

 \=\=\=

- **Programmer: US only (Country Code \= 27\)**
- **SINGLE ANSWER**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | White |
| 2 | Black or African\-American |
| 3 | Asian or Pacific Islander |
| 4 | American Indian or Alaskan Native |
| 5 | Mixed racial background |
| 6 | Other race |
| 99 | Prefer not to answer |

 \*\*\*

 **EDUCATION\_C****:** What is your highest level of education?

 \=\=\=

- **SINGLE ANSWER**
- **Programmer: Do not display scale numbers**
- **Refer to codebook for each country**
- **Include Hidden “Education” for High, Middle, low – See codebook**

 \*\*\*

 **INCOME\_C:** What is your household’s annual income before taxes?

 \=\=\=

- **SINGLE ANSWER**
- **Refer to codebook for each country**
- **Programmer: Do not display scale numbers**
- **Include HIDDEN variable “Income” for High, Middle, Low – See codebook for classifications**

 \*\*\*

 **ONLY ASK PARTY IF COUNTRY\=UNITED STATES (CODE\=27\)**

 **PARTY****:** Regardless of how you may vote, what do you usually consider yourself …

 \=\=\=

- **Programmer: US only (Country Code \= 27\)**
- **SINGLE ANSWER**

 **VARIABLES TABLE**

| **Value Code** | **Value Label** |
| 1 | Republican |
| 2 | Democrat |
| 3 | Independent |
| 98 | Other party (please specify \_\_\_\_\_\_\_) **\[TEXT BOX]** |
| 99 | Prefer not to answer |

 \*\*\*

# Section 9000 \- Closing

 **Q9000****\[SCREENER]**: Thank you for completing this study.

 For more information on The RepTrak Company please visit: [www.reptrak.com](http://www.reptrak.com/)

 \=\=\=

 \*\*\*

 Confidential 36