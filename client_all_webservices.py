from suds.client import Client
import readline
import base64
#from optparse import OptionParser
import sys
import logging
import datetime
import pprint
#from client_bnfinder import client_bnfinder
#import pdb

def throw_exception(val):
    if val == "":
        raise Exception("This Field Can Not Be Blank!")
        fl = 0
    else:
        fl = 1
    return fl

def rlinput(prompt, default=''):
    readline.set_startup_hook(lambda: readline.insert_text(default))
    flag = 0
    while not flag == 1:
        try:
            v = raw_input(prompt).strip()
            flag = throw_exception(v)
            return v
        except Exception as e:
            print "Attention!: ", e.args[0]
        finally:
            readline.set_startup_hook()

def print_bs(tab, nrow_start= 11, nrow_end = 5, sep = '[...]'):
	tab = base64.b64decode(tab)
	tmp = tab.split('\n')
	print '\n'.join(tmp[:nrow_start])
	if not nrow_end == 0:
		nrow = len(tmp)
		print sep
		print '\n'.join(tmp[(nrow-nrow_end):nrow])


sys.stdout.write("\nCONNECTING TO THE WEBSERVICE. PLEASE WAIT FOR A WHILE... :) \n")
global client
client = Client("http://212.87.20.245:8080/expression?wsdl", timeout=10000, cache=None)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

### SECTION I: GENE-EXPRESSION DATA ANALYSIS ###

### 1. GetDataFromFiles(xs:base64Binary file_data, xs:base64Binary file_row_attr, xs:base64Binary file_col_attr, DatasetInfo dataset__info, ), output: NgpObject

#This function creates NgpObject from the tab-separated files. Three different files describe one dataset. First file_data contains the main data with the unique row and column names.
#The files: file_row_attr and file_col_attr contain other attributes if they exist. The first column and row in other attributes files must be the same as in the main data file.
#If 'main' attributes in other attributes files are in differ column then the name of attributes must be the same and new main index will be set and the data will be duplicated.
#Only one of the files is necessary to build the NgpObject.

### Uncomment the following section to invoke the Read_data_from_file client!
def read_data_from_file():
    sys.stdout.write("\nMESSAGE: *** YOU HAVE INVOKED THE READ_DATA_FROM_FILE CLIENT ***\n")
    data_file = rlinput("\nPlease type the pathname of the data file: ") #data
    row_file = rlinput("\nPlease type the pathname of the row-attributes file: ") #row
    global column_file
    column_file = rlinput("\nPlease type the pathname of the column-attributes file: ") #col
    data_name = rlinput("\nDataset Name: ", "NONE") #infor
    data_desc = rlinput("\nDataset Description: ", "NONE")

    try:
        #call the read_file webservice:
        sys.stdout.write("\nMESSAGE: *** THE FILE OBJECT FORMAT IS BEING CONVERTED. PLEASE WAIT FOR A FEW MOMENTS... ***\n")
        # create DatasetInfo object:
        data_info = client.factory.create("DatasetInfo")
        data_info.dataset__name = data_name
        data_info.dataset__description = data_desc

        data_object = client.service.GetDataFromFiles(file_data= base64.b64encode(open(data_file,'r').read()), file_row_attr= base64.b64encode(open(row_file,'r').read()), file_col_attr= base64.b64encode(open(column_file,'r').read()),dataset__info= data_info)

        sys.stdout.write("\nMESSAGE: *** THE OBJECT IS READY NOW! ***\n")
    except:
        print 'Read_data_from_file Failed. Details: %s' % sys.exc_info()[1]
    return data_object, data_name, data_desc, data_info

data_obj, data_name, data_desc, data_info = read_data_from_file()

sys.stdout.write("\nMESSAGE: *** THE COLUMN ATTRIBUTES OF YOUR DATA ARE AS FOLLOWS: ***\n\n")

with open(column_file, "r") as col_f:
    col_data_all = col_f.readlines()
    print '\n'.join(col_data_all[:])

plot_col_attr_names = col_data_all[0].rstrip("\n").split("\t")
print plot_col_attr_names

treat_col_name = rlinput("\nPlease Type the Column-Attribute Name of the Column that Contains the Names of Control and Treatment Groups: ")
control_name = rlinput("\nPlease Type the Name of Your Control Group (which is a Column-Attribute Value within the Column with Column-Attribute Name Above): ")
### "Data-Beauty-Parlour" Section! Pre-processing. Activate if you need to transform and mean-center your data. ###
# The methods marked with **** are used here for a)sorting the control columns together in the begiinig (TakeByColumnRow), b) mean-centering the data etc.
# These **** marked methods are mentioned separately in the bottom half of this script as well, so that the user may use them for different purpose.

### You can reorder the columns of your datafile for the purposes like keeping the control group together, etc. using TakeByColumnRow. For other uses see at the bottom of the script.
### **** 14. TakeByColumnRow(NgpObject dataset, OtherAttrArray selected_rows_columns, DatasetInfo dataset_info, ), output: NgpObject

# This function returns a subset of dataset. Specify the columns and/or rows names to extract in selected_rows_columns argument.
# The OtherAttr is part of NgpObject and contain following fields: attr__name - name of column/row attributes, attr__value - column/row value, and attr__type - 'row' or 'column'.

#### Tester's comment 1: input_col.attr__values is mentioned as input_col.attr__value in documentation. Missing "s".

sys.stdout.write("\nMESSAGE: *** YOU CAN REORDER YOUR DATA COLUMNS IF YOU NEED, e.g., REORDER THE COLUMNS TO KEEP controls, treatment_1, and treatment_2 COLUMNS RESPECTIVELY TOGETHER ***\n")
reorder_choice = rlinput("\nDo You Want to Reorder Your Data-columns?[yes/no]: ", "yes")
if reorder_choice.lower() == "yes":
    col_attr_name = treat_col_name #rlinput("\nPlease Provide the Column Attribute Name: ")
    attr_vals= []
    input_attr_vals = rlinput("\nPlease Provide the Column Attribute Values in the Following Comma-separated Format: ctrl, treatment_1, treatment_2, ... : ")
    #input_attr_vals = input_attr_vals.strip()
    if input_attr_vals.endswith(","):
        attr_vals.extend(input_attr_vals.split(",")[:-1])
    else:
        attr_vals.extend(input_attr_vals.split(",")[:])
    col_attr_vals = [ele.strip() for ele in attr_vals]
    print col_attr_vals
    try:
        # here you can mention only the column specification and data from corresponding columns from all the rows will be retreived.
        input_col = client.factory.create("OtherAttr")
        input_col.attr__values = {"string": col_attr_vals} #{"string": ["gcm","mgcm","lps"]}
        input_col.attr__name = col_attr_name #"treatment"
        input_col.attr__type = "column"
        
        input__list = {"OtherAttr": [input_col]}
        
        take_result_obj = client.service.TakeByColumnRow(dataset= data_obj, selected_rows_columns= input__list, dataset_info= data_info)
        encoded_take_result = client.service.ReturnDataAsTSV(take_result_obj)
        #print '\n'.join(base64.b64decode(encoded_take_result[0]).split('\n')[:10])
        print_bs(encoded_take_result[0])
        #print str(base64.b64decode(encoded_take_result[1]))
        #print str(base64.b64decode(encoded_take_result[2]))
        data_obj = take_result_obj
    except:
        print 'TakeByColumnRow() Failed. Details: %s' % sys.exc_info()[1]
else:
    data_obj = data_obj

### 2. DatasetFunction(NgpObject dataset, xs:string function, ), output: NgpObject
#This function returns the result of one of the methods listed below as NgpObject.
#A full list of function parameter:

#    exp: calculate the exponential of all elements in the input dataset,
#    expm1: calculate exp(x) - 1 for all elements in the input dataset,
#    exp2: calculate 2**p for all p in the input dataset,
#    log: natural logarithm, element-wise,
#    log10: return the base 10 logarithm of the input dataset, element-wise,
#    log2: return the base 2 logarithm of the input dataset, element-wise,
#    log1p: return the natural logarithm of one plus the input dataset, element-wise,
#    sin: trigonometric sine, element-wise,
#    cos: cosine elementwise,
#    tan: compute tangent element-wise,
#    arcsin: inverse sine, element-wise,
#    arccos: trigonometric inverse cosine, element-wise,
#    arctan: trigonometric inverse tangent, element-wise,
#    degrees: convert angles from radians to degrees,
#    radians: convert angles from degrees to radians,
#    deg2rad: convert angles from degrees to radians,
#    rad2deg: convert angles from radians to degrees,
#    sinh: hyperbolic sine, element-wise,
#    cosh: hyperbolic cosine, element-wise,
#    tanh: hyperbolic cosine, element-wise,
#    arcsinh: inverse hyperbolic sine element-wise,
#    arccosh: inverse hyperbolic cosine, element-wise,
#    arctanh: inverse hyperbolic tangent elementwise,
#    rint: round elements of the dataset to the nearest integer,
#    floor: return the floor of the dataset, element-wise,
#    ceil: return the ceiling of the input, element-wise,
#    trunc: return the truncated value of the dataset, element-wise,
#    sqrt: return the positive square-root of an array, element-wise,
#    square: return the element-wise square of the input dataset,
#    absolute: calculate the absolute value element-wise,
#    fabs: compute the absolute values elementwise,
#    sign: returns an element-wise indication of the sign of a number.

### 3. ReturnDataAsTSV(NgpObject dataset, ), output: tsv
#This function returns a dataset as the tab-separated files.

sys.stdout.write("\nMESSAGE: *** THIS SECTION CAN BE USED FOR log2 TRANSFORMATION OF YOUR DATA ***\n")
log_trans = rlinput("\nWould You Like to log-transform Your Data?[yes/no]: ", "no")
if log_trans.lower() == "yes":
    try:
        log_data_obj = client.service.DatasetFunction(data_obj, function="log2")
        data_obj = log_data_obj
        log_tsv = client.service.ReturnDataAsTSV(log_data_obj)
        for i in range(len(log_tsv)):
            print base64.b64decode(log_tsv[i])
    except:
        print 'log2 transformation of input-dataset Failed. Details: %s' % sys.exc_info()[1]
else:
    data_obj = data_obj

### Mean-centering Data!

### 4. GroupByDataset(NgpObject dataset, DatasetInfo dataset_info, xs:string group_attr, xs:string count_attr, xs:string per, stringArray functions, ), output: NgpObject
#This function categorizes the dataset and applies the function(s) (functions) on each group. The dataset is split into groups based on one or more keys (group_attr). This splitting is performed on the rows (per=row) or the columns (per=column). By default, it's performed on the rows and compute mean and standard deviation of values. The fields group_attr and dataset are mandatory. Additionally you can sum in how many groups the defined attributes (count_attr) occur in- an extra column will be added to column/row attributes.

#A full list of functions:

#    mean: mean of values,
#    sum: sum of values,
#    count: number of non-NA values in the group,
#    median: arithmetic median of values,
#    std: standard deviation,
#    var: variance,
#    min: minimum of values,
#    max: maximum of values,
#    prod: product of non-NA values,
#    first: first non-NA value,
#    last: last non-NA value.

#The user can pass more than one of above methods.
#In the results the column/row names contain a suffix with name of the function (e.g. my_column__mean).

### **** 10. DatasetOperator(NgpObject dataset, DatasetInfo dataset_info, xs:string operator, NgpObject dataset2, xs:string axis_name, xs:string per, ), output: NgpObject
#Mentioned separately below at No 10 as well.
#This function makes arithmetic operation between dataset and column/row (axis_name) from dataset2. It can be done across the rows (per=row) or the columns (per=column).
# For example, if you want to add values from column (axis_name) of dataset2 to dataset by matching the rows then define: axis_name: my_column_name, per: column, operation: add.
#Operator:

#    add: method for addition (+)
#    sub: method for subtraction (-)
#    div: method for division (/)
#    mul: method for multiplication (*)

# the first dataset is taken from the previous work-flow or output of read_data_from_file() function's first call. namely: data_obj

sys.stdout.write("\nMESSAGE: *** THIS SECTION CAN BE USED FOR MEAN-CENTERING YOUR DATA ***\n")
mean_cent_choice = rlinput("\nDo You Want to Mean-Center Your Data?[yes/no]: ", "yes")

if mean_cent_choice.lower() == "yes":
    grp_name = treat_col_name #rlinput("\nPlease Provide the Column Attribute Name (which Contains the Attribute Values about Control and Treatment Groups): ")
    ##grp_name = "treatment" 
    #count_attr = 'description' # Please mention the name of the column that contains descriptions of corresponding Control and Treatment Groups
    
    dataset_used = data_obj
    #funcList = {"string": ["mean"]} # This is how to pass the list of functions. Example-1.
    #funcList = {"string": ["median", "sum"]} # Example-2.
    try:
        mean_cent_data_obj = client.service.GroupByDataset(dataset=dataset_used, dataset_info=data_info, group_attr= grp_name, per="column") # no "functions" passes default: mean and std
        #mean_cent_data_obj = client.service.GroupByDataset(dataset=dataset_used, dataset_info=data_info, group_attr= grp_name, per="column", functions= funcList, count_attr=count_attr)
        mean_cent_data_tsv_obj = client.service.ReturnDataAsTSV(mean_cent_data_obj)
        #print base64.b64decode(mean_cent_data_tsv_obj[0])
        print_bs(mean_cent_data_tsv_obj[0])
        #print base64.b64decode(mean_cent_data_tsv_obj[2])
    except:
        print 'Group_by_Dataset Failed. Details: %s' % sys.exc_info()[1]
    
    #sys.stdout.write("\nMESSAGE: *** YOU HAVE PROVIDED THE COLUMN ATTRIBUTE NAME (THAT CONTAINS THE ATTRIBUTE VALUES ABOUT CONTROL AND TREATMENT GROUPS) ABOVE. \n")
    #sys.stdout.write("\n     ... NOW PLEASE PROVIDE THE COLUMN ATTRIBUTE VALUE (HOW YOU CALL IT!) FOR YOUR CONTROL. THE CORRESPONDING MEAN OF THIS CONTROL GROUP WILL BE SUBTRACTED FROM CORRESPONDING DATA. ***\n")
    name_axis = control_name #rlinput("\nPlease Provide the Column Attribute Value of Control Group: ")
    name_axis = name_axis + "__mean"
    try:
        #dataset_2, dataset_2_name, dataset_2_desc, dataset_2_info = read_data_from_file()
        dataset_1 = data_obj
        dataset_2 = mean_cent_data_obj
        op_result_obj = client.service.DatasetOperator(dataset= dataset_1, dataset_info= data_info, operator= 'sub', dataset2= dataset_2, axis_name= name_axis, per='column')
        encoded_op_result = client.service.ReturnDataAsTSV(op_result_obj)
        #print str(base64.b64decode(encoded_op_result[0]))
        print_bs(encoded_op_result[0])
        data_obj = op_result_obj
    except:
        print 'DatasetOperator() Failed. Details: %s' % sys.exc_info()[1]
else:
    data_obj = data_obj


###  Do_Statistical_Tests (t-test and ANOVA)
### 5. DoTtest(NgpObject dataset, InputStat input_Ttest, ), output: NgpObject
#This function calculates the t-test for the means of two independent samples of scores. Define the groups to compare in input_Ttest argument. The function returns p-value, T-statistics and difference of means (diff_mean).
### 6. DoAnova(NgpObject dataset, InputStat input_Anova, ), output: NgpObject
#This function performs one-way ANOVA. Define the groups to compare in input_Anova argument. The function returns a p-value and F-value.

### Remove the Docstring quotes in the following section to invoke Do_Statistical_Tests clients!
# Start of Do_Statistical_Tests #

sys.stdout.write("\nMESSAGE: *** THIS IS THE SECTION FOR STATISTICAL ANALYSIS OF THE DATA. ***\n")
do_stat_choice = rlinput("\nWould You Like to Perform Some Statistical Tests (t-test/ANOVA) on Your Data? [options: yes/no]: ", "yes")
if do_stat_choice.lower() == "yes":
    sys.stdout.write("\nMESSAGE: *** YOU HAVE INVOKED THE DO_STATISTICS CLIENT ***\n")
    # prepare arguments:
    ngp_obj = data_obj
    groups1 = []
    option = rlinput("\nWhat Would You like to Do? \noptions: T (for t-test)/ A (for ANOVA): ", default= "T")
    attr_col_name = treat_col_name #rlinput("\nPlease type the attribute column name: ") #row
    if option == "T":
        T_grp_1 = rlinput("\nPlease provide the names of the first group: ") #col
        groups1.append(T_grp_1)
        T_grp_2 = rlinput("\nPlease provide the names of the second group: ")
        groups1.append(T_grp_2)
    elif option == "A":
        A_grps = rlinput("\nPlease provide the names of the groups, separated by comma: group1, group2, ...,groupN : ")
        #A_grps = A_grps.strip()
        if A_grps.endswith(","):
            groups1.extend(A_grps.split(",")[:-1])
        else:
            groups1.extend(A_grps.split(",")[:])
    groups = [ele.strip() for ele in groups1]
    print groups
    
    if option == "T":
        stat_name = "t-test"
    else:
        stat_name = "ANOVA"
    try:
        sys.stdout.write("\nMESSAGE: *** %s IS BEING PERFORMED ON YOUR SELECTED DATA ***\n"%(stat_name))

        #create InputStat object
        input_stat = client.factory.create("InputStat")
        input_stat.attr_col_name = attr_col_name
        input_stat.groups = {"string": groups}
        #print input_stat
        # call the web services for statistical tests:
        if option == "T":
            ttest_obj = client.service.DoTtest(ngp_obj, input_Ttest= input_stat)
            stat_obj = ttest_obj
            #print "t-test object is ready!!"
            tsv_obj= client.service.ReturnDataAsTSV(ttest_obj)
        else:
            anova_obj = client.service.DoAnova(ngp_obj, input_Anova= input_stat)
            stat_obj = anova_obj
            tsv_obj= client.service.ReturnDataAsTSV(anova_obj)
        # for writing data to file, uncomment the following lines:
        sys.stdout.write("\nMESSAGE: *** PLEASE FIND THE RESULTS IN THE FOLLOWING FILE IN THE PRESENT DIRECTORY: %s_output_%s.txt ***\n"%(stat_name,data_name))
        time = datetime.datetime.now()
        with open("%s_output_%s.txt"%(stat_name,data_name), "w")as f_stat:
            file_intro_stat = "### Result of %s performed on %s dataset. The following reference groups: %s were chosen from the column: %s.\n### %s\n"%(stat_name,data_name,str(groups),attr_col_name,time)
            f_stat.write(file_intro_stat)
            f_stat.write(str(base64.b64decode(tsv_obj[0])))
    except:
        print 'Do_Statistics Failed. Details: %s' % sys.exc_info()[1]

# End of Do_Statistical_Tests #


### Cut Client ###

### 6. CutData(NgpObject dataset, NgpObject dataset_2, ConditionObject condition, DatasetInfo dataset_info, ), output: NgpObject

#This function selects a subset of the rows from the dataset (variable: dataset) using given conditions (variable: condition). If the function is called without dataset_2 argument then the conditions refer to the dataset variable. In other case all the conditions refer to the dataset(s) defined in dataset_2 parameter. The 'ConditionObject' defines which column name(s) fulfill given criteria (e.g. select the rows from dataset where values from column(s) (col_name) are less/greater/equal/not_equal then value e.g. '0.1'.

### Remove the Docstring quotes in the following section to invoke Cut client!
# Start of Cut_client_section #

if do_stat_choice.lower()== "yes":
    sys.stdout.write("\nMESSAGE: *** YOU PERFORMED STATISTICAL TESTS ON YOUR DATA. YOU MAY CONTINUE WITH YOUR ENTIRE DATASET. OR, YOU CAN RETRIEVE (CUT) PART OF YOUR DATA BASED ON SOME THRESH-HOLD STATISTIC-VALUE ***\n")
    cut_choice =  rlinput("\nDo You Want to Cut Your Data?[options: yes/no]: ", "yes")
    if cut_choice.lower() == "yes":
        sys.stdout.write("\nMESSAGE: *** YOU HAVE INVOKED THE CUT_CLIENT ***\n")
        data_obj_1 = data_obj
        data_obj_2 = stat_obj #choose any one between ttest_obj and anova_obj as per your options in Do_Statistics!
        condition = rlinput("\nPlease Provide the Condition for Cutting Data: ", "pval LESS 0.5")
        try:
            sys.stdout.write("\nMESSAGE: *** THE CUT OPERATION IS BEING PERFORMED. PLEASE WAIT FOR A FEW MOMENTS... ***\n")
            data_info_stat = client.factory.create("DatasetInfo")
            data_info_stat.dataset__name = data_name
            data_info_stat.dataset__description = data_desc

            #call webservice
            cut_obj_1, cut_obj_2 = client.service.CutData(data_obj_1, data_obj_2, condition, data_info_stat) #cut_obj_1 is of importance for further use down the line.
            # for writing data to file, uncomment the following lines:
            encoded_file_cut = client.service.ReturnDataAsTSV(cut_obj_1)
            sys.stdout.write("\nMESSAGE: *** PLEASE FIND THE RESULTS OF CUT OPERATION IN THE FOLLOWING FILE IN THE PRESENT DIRECTORY: cut_data_output_%s.txt ***\n"%(data_name))
            time = datetime.datetime.now()
            with open("cut_data_output_%s.txt"%(data_name), "w")as f_cut:
                file_intro = "### Result of CutData operation performed on %s dataset.\n### %s\n"%(data_name,time)
                f_cut.write(file_intro)
                f_cut.write(str(base64.b64decode(encoded_file_cut[0])))
            data_obj = cut_obj_1[1]
            #print data_obj
        except:
            print 'Cut Operation Failed. Details: %s' % sys.exc_info()[1]
    else:
        data_obj = data_obj
# End of Cut_client_section #

### Cluster Client
### **** 7. DoCluster(NgpObject dataset, gap_stat, no_cluster), output: NgpObject
#This function computes k-means clustering. (used in this flow together with DoPlot. See below for stand-alone.)

### Plot Client ###

### 8. DoPlot(NgpObject datasets, InputPlot input_plot, ), output: pdf

#Mandatory arguments: datasets, function
#Optional arguments: colors, width_size, hight_size, attr_row__name, attr_col__name, norm_color, cmap, with_cluster, vmin, vmax, legend, cbar_legend, cbar_legend_side, per_col
#Description: This function plots a graphical representation of dataset(s). The user can simply customize a plot (input_plot); the colors,width_size and hight_size arguments are available in each plot method, others arguments are depended on selected plot method. The result is returned in pdf format (dpi=300).

#A full list of plot methods:

# a)    heatmap: by default, the colormap is normalized by calculating maximum absolute value of minimum or maximum value of the dataset.
#       If not normalize colormap just set norm_color: False and then the maximum and minimum value of dataset will be used to autoscaled the color.
#       The user can set manually the scale of color by passing vmin and vmax values. By default, the legend of colormap is localised in the bottom of the plot (cbar_legend: True, cbar_legend_side: bottom).
#       The user can change localisation of it on the left-side of the plot by passing the cbar_legend_side: left, or remove the legend by setting cbar_legend: False.
#       The heatmap will be plot with labels (legend: True) if number of the rows is less than 500, otherwise the legend of y axis will be removed. To remove the labels set legend: False.
#       The labels can be customized by attr_row__name and attr_col__name arguments.
#       By default, the jet colormap is used, to changed it pass the other colormap in parameter cmap. To choose one of colormap see                                                                                        cmap_color_list (http://www.nencki-genomics.org/webservices/lib/exe/fetch.php?media=tutorial:cmap.pdf).
#       Additional options is with_cluster arguments. If this arguments is set True than two datasets must be passed in dataset argument. The second dataset is the result of clustering of the first dataset.              The clusters will be added on the plot.

# b)    expr_profile: method for plotting gene expression profiles. By default, all rows (genes) are plotted.
#       The user can plot selected rows (genes) from the dataset in different color by passing them in attr_row__name argument.
#       To plot selected rows with one color set legend: False.
#       The labels of x axis can be customized by attr_col__name.
#       Additionally the user can plots the rows (genes) from differ cluster on separated subplots by setting with_cluster: True and adding the result of clustering to dataset argument as second dataset.

# c)    scatter: by default, the function plots all the scatter plots among a group of variables, i.e. scatter matrix plot.
#       To plot a simple scatter plot define the names of columns in attr_col__name parameter. The order of column names is important - they are splitted into pairs and plotted separately.
#       To remove legend set legend: False.

# d)    barplot: by default, generates a bar plot showing the mean and standard deviation of dataset for each row (per_col: False). To change it set per_col: True.
#       The user can customize labels by attr_row__name (if per_col: False) or attr_col__name (if per_col: True).

### Remove the Docstring quotes in the following section to invoke Plot client!
# Start of Plot_client_section #

sys.stdout.write("\nMESSAGE: *** THIS SECTION FINALLY PLOTS YOUR DATA ***\n")
plot_choice = rlinput("\nDo You Want to Plot Your Data?[options: yes/no]: ", "yes")
if plot_choice.lower() == "yes":
    sys.stdout.write("\nMESSAGE: *** YOU HAVE INVOKED THE PLOT_CLIENT ***\n")
    plot_data_obj_1 = data_obj #cut_obj_1  # OR stat_obj which is the result of ttest/ anova operation.
    #plot_data_obj_1 = stat_obj
    #sys.stdout.write("\n*** If you want to add clusters of your data to be added on the plot, you are required to cluster your data. ***\n")
    #cluster = rlinput("\nDo You Want to Cluster Your Data?[options: 1.yes, 2.no]: ", "no")
    sys.stdout.write("\n*** FOLLOWING ARE THE AVAILABLE PLOT METHODS: 1. heatmap, 2. expr_profile, 3. scatter, 4.barplot ***\n")
    function = rlinput("\nWhat Kind of Plot Do You Want? : ", "heatmap")
    cluster = False
    if function== "heatmap" or function== "expr_profile":
        sys.stdout.write("\nMESSAGE: *** IF YOU WANT TO VISUALIZE CLUSTERS OF YOUR DATA ON THE PLOT, YOU ARE REQUIRED TO CLUSTER YOUR DATA FIRST. ***\n")
        cluster_choice = rlinput("\nDo You Want to Cluster Your Data?[options: yes/no]: ", "no")
    
    #input_plot_options = custom_plot_opts(function)
        if cluster_choice.lower() == "no":
            cluster = cluster
        else:
            cluster = True
            # prompt for number of clusters and gap statistic
            sys.stdout.write("\nMESSAGE: *** THE PROGRAM CAN CALCULATE THE NUMBER OF CLUSTERS FROM THE DATA. OR, YOU MAY MANUALLY PROVIDE THE NUMBER OF CLUSTERS YOU WANT. ***\n")
            num_cluster_choice = rlinput("\nDo You Want to Provide the Number of Clusters Manually?[options: yes/no]: ", "no")
            num_cluster_choice = num_cluster_choice.lower()
            num_cluster_choice_set = ["yes", "no"]
            if num_cluster_choice in num_cluster_choice_set:
                if num_cluster_choice == "no":
                    num_cluster = False
                else:
                    user_num_clust = int(rlinput("\nPlease Provide the Number of Clusters Manually[example: 5]: "))
                    num_cluster = user_num_clust #int(user_num_clust)
            else:
                print "You have provided illegal value!! You are funny!"

            stat_score_choice = rlinput("\nBetween Gap-score and Silhouette-Score, Which Statistic Do You Want to Use?[options: gap/sil]: ", "gap")
            stat_score_choice = stat_score_choice.lower()
            if stat_score_choice == "gap":
                gap_stat_chosen = True
            else:
                gap_stat_chosen = False
    try:
        #For the attributes of input_plot, if you want their default values to be passed, then you do NOT have to change anything (i.e., you do not have to uncomment the coresponding line). If you want values other than the default values to be passed, then uncomment the corresponding line and change the value as per your requirement. The choices are mentioned in each of the line.
        input_plot = client.factory.create("InputPlot")
        input_plot.function = function
        if cluster: input_plot.with_cluster = True
        
        ### COMMON CUSTOM OPTIONS FOR PLOT-FUNCTION(S): heatmap, expr_profile, scatter, barplot [all the options]
        #input_plot.colors = ["g"] #, "r", "b"]
        #input_plot.width_size = 5 #input_plot_options["width_size"]
        #input_plot.height_size= 10 #input_plot_options["height_size"]

        # input_plot.attr_col__name SECTION BELOW:
        col_attr_dict = {}
        for num_attrs in range(len(plot_col_attr_names)):
            col_attr_dict["col_attr_name_{0}".format(num_attrs+1)] = client.factory.create("AttrName")
        #print col_attr_dict
        s_keys = sorted(col_attr_dict)
        #print s_keys
        for key in s_keys: # sorted(col_attr_dict):
            col_attr_dict[key].name = plot_col_attr_names[s_keys.index(key)]
        #print col_attr_dict
        attr_name_list = [col_attr_dict[k] for k in s_keys]
        input_plot.attr_col__name = {"AttrName": attr_name_list}
        #print input_plot.attr_col__name
        
        ### SPECIFIC CUSTOM OPTIONS FOR PLOT-FUNCTION(S): heatmap
        #input_plot.norm_color = False #input_plot_options["norm_color"]
        #input_plot.vmin= -6 #input_plot_options["vmin"]
        #input_plot.vmax= 6 #input_plot_options["vmax"]
        #input_plot.cmap = "gist_earth_r" # default: "jet" #input_plot_options["cmap"]
        #input_plot.cbar_legend= # Choices" True, False (boolean). Default: True. Choose False if you do not want any color bar legend. # input_plot_options["cbar_legend"]
        #input_plot.cbar_legend_side = "left" #Define the positions of color bar legend. Choices: "left" or "bottom". Default: "bottom". Modify ONLY IF you want to provide the value "left". Else the webservice automatically gets the value "bottom", even if it is not specifically mentioned here.  #input_plot_options["cbar_legend_side"]
        ###
        
        ### SPECIFIC CUSTOM OPTIONS FOR PLOT-FUNCTION(S): heatmap, expr_profile, and scatter.
        #input_plot.legend= False ##Deafult: True. (a)for heatmap: You can change the value to False if you do not want any LABELS of rows. (b) for expr_profile: If legend is False (expr_profile) then all rows (genes) will be plotted as the same color. AND it will remove the LEGEND in the figure.
        ###
        ### SPECIFIC CUSTOM OPTIONS FOR PLOT-FUNCTION(S): barplot
        #input_plot.per_col = True ##Default = False. If True, the columns are used to plot the bars, otherwise the rows are used.
        ###
        
        if not cluster: #input_plot_options["with_cluster"]: # if cluster option is False
            sys.stdout.write("\nMESSAGE: *** THE PLOT OPERATION IS BEING PERFORMED: CLUSTER_MODE: OFF. PLEASE WAIT FOR A FEW MOMENTS... ***\n")
            x = client.service.DoPlot(datasets= plot_data_obj_1, input_plot= input_plot)
        else:
            sys.stdout.write("\nMESSAGE: *** YOUR SELECTED DATA IS BEING CLUSTERED ***\n")
            try:
                if num_cluster == False:
                    plot_cluster_obj = client.service.DoCluster(plot_data_obj_1, gap_stat= gap_stat_chosen)
                else:
                    plot_cluster_obj = client.service.DoCluster(plot_data_obj_1, gap_stat= gap_stat_chosen, no_cluster= num_cluster)
            except:
                print 'Cluster Failed. Details: %s' % sys.exc_info()[1]

            sys.stdout.write("\nMESSAGE: *** THE PLOT OPERATION IS BEING PERFORMED: CLUSTER_MODE: ON. PLEASE WAIT FOR A FEW MOMENTS... ***\n")
            x = client.service.DoPlot(datasets= plot_data_obj_1, cluster_data= plot_cluster_obj, input_plot= input_plot)
        
        #for writing to file:
        x_decoded = base64.b64decode(x)
        with open("plot__result_%s_%s"%(data_name,function),"w") as f:
            f.write(x_decoded)
        sys.stdout.write("\nMESSAGE: *** YOUR PLOT IS READY!! PLEASE FIND IT IN THE PRESENT DIRECTORY ***\n")
    
    except:
        print 'Plot Operation Failed. Details: %s' % sys.exc_info()[1]

# End of Plot_client_section #

### SECTION II: GENE REGULATION ###

# 1. Start of BNFinder_Client_Section #
### The Bnfinder Web Service is a remote interface to the Bnfinder program, a tool to learn Bayesian networks from data. Its main aim is to provide a way to analyze relations between trancription factors and gene expression patterns using Bayesian networks. (Details Here: http://biquad.mimuw.edu.pl/)
"""
try:
    bnf_data_obj = data_obj
    sys.stdout.write("\nMESSAGE: *** YOUR SELECTED DATA IS BEING CLUSTERED ***\n")
    bnf_cluster_obj = client.service.DoCluster(bnf_data_obj)
    sys.stdout.write("\nMESSAGE: *** CONNECTING TO THE BNfinder WEBSERVICE. PLEASE WAIT FOR A WHILE. ***\n")
    bnfinder_job_id = client_bnfinder(bnf_cluster_obj)
    sys.stdout.write("\n*** Your BNFinder JOB_ID is: %s"%(bnfinder_job_id))
except:
    print 'BNFinder Operation Failed. Details: %s' % sys.exc_info()[1]
"""
# End of BNFinder_Client_Section #

### SECTION III: Other Methods of NEWS- Examples ###
### Outside the Main Workflow: Examples for other methods:

### 9. DatasetFunPerRowCol(NgpObject dataset, stringArray function, xs:string per, ), output: NgpObject
# This function extracts a single value (the result of function e.g. sum or mean) from the rows or columns of a dataset. The per variable defines if a function will be applied over the rows (per=row) or columns (per=column). Default per=row.
# A full list of function parameter:

#    count: number of non-NA values,
#    min: compute minimum values,
#    max: compute maximum values,
#    quantile: compute sample quantile ranging from 0 to 1,
#    sum: sum of values,
#    mean: mean of values,
#    median: arithmetic median (50% quantile) of values,
#    mad: mean absolute deviation from mean value,
#    var: sample variance of values,
#    std: sample standard deviation of values,
#    skew: sample skewness (3rd moment) of values,
#    kurt: sample kurtosis (4th moment) of values.

#The user can pass more than one of above methods.
"""
try:
    #auth = client.factory.create("Authenticate")
    #auth.username = "sam"
    ##auth.is_public = "N"
    #auth.password = "ibdsam50"

    #dataset_id = 1
    #data_from_db = client.service.GetDataFromDb(authenticate = auth, dataset_id = dataset_id)
    #print data_from_db
    
    fun_dataset = data_obj
    #### IZA LINE
    functionList = {'string': ['mean','std']}

    fun_result_obj= client.service.DatasetFunPerRowCol(dataset= data_obj, function= functionList, per= "row")
    #print fun_result_obj
    encoded_fun_result = client.service.ReturnDataAsTSV(fun_result_obj)
    print str(base64.b64decode(encoded_fun_result[0]))
except:
    print 'DatasetFunPerRowCol() Failed. Details: %s' % sys.exc_info()[1]
"""
### 10. DatasetOperator(NgpObject dataset, DatasetInfo dataset_info, xs:string operator, NgpObject dataset2, xs:string axis_name, xs:string per, ), output: NgpObject

#This function makes arithmetic operation between dataset and column/row (axis_name) from dataset2. It can be done across the rows (per=row) or the columns (per=column).
# For example, if you want to add values from column (axis_name) of dataset2 to dataset by matching the rows then define: axis_name: my_column_name, per: column, operation: add.
#Operator:

#    add: method for addition (+)
#    sub: method for subtraction (-)
#    div: method for division (/)
#    mul: method for multiplication (*)

# the first dataset is taken from the previous work-flow or output of read_data_from_file() function's first call. namely: data_obj
"""
try:
    #dataset_2, dataset_2_name, dataset_2_desc, dataset_2_info = read_data_from_file()
    dataset_2 = mean_cent_data_obj
    op_result_obj = client.service.DatasetOperator(dataset= data_obj, dataset_info= data_info, operator= 'sub', dataset2= dataset_2, axis_name= 'gcm__mean', per='column')
    #op_result_obj = client.service.DatasetOperator(dataset= data_obj, dataset_info= data_info, operator= 'sub', dataset2= dataset_2, axis_name= 'RAT_1.CEL', per='column') #working general example
    encoded_op_result = client.service.ReturnDataAsTSV(op_result_obj)
    print str(base64.b64decode(encoded_op_result[0]))
except:
    print 'DatasetOperator() Failed. Details: %s' % sys.exc_info()[1]
"""
### 11. MergeData(NgpObject dataset, NgpObject dataset_2, DatasetInfo dataset_info, xs:string method), output: NgpObject ; (method: one of:outer, inner, left, right)

#This function combine datasets by linking the row names using one of the methods: outer, inner, left, right; the inner method by default. The user can pass more than one dataset in dataset_2 argument. In case of the column names overlapping the suffixes will be added e.g. if data in both datasets, would appear as 'data__[dataset_id]' and 'data__[dataset_id]' in result where 'dataset_id' is defined in NgpObject (if not then 0,1.. will be used).
#Methods:

#    inner: use intersection of row names from both datasets
#    outer: use union of row names from both datasets
#    left: the datasets will be merged on the left side, i.e. use only row names from dataset
#    right: the datasets will be merged on the right side, i.e. use only row names from dataset_2
"""
try:
    dataset_2_obj, dataset_2_name, dataset_2_desc, dataset_2_info = read_data_from_file()
    #print dataset_2_obj
    merge_result_obj = client.service.MergeData(dataset= data_obj, dataset_2= dataset_2_obj, dataset_info= data_info, method= 'outer')
    encoded_merge_result = client.service.ReturnDataAsTSV(merge_result_obj)
    print str(base64.b64decode(encoded_merge_result[0]))
except:
    print 'MergeData() Failed. Details: %s' % sys.exc_info()[1]
"""
### 12. SortColumnsRows(NgpObject dataset, DatasetInfo dataset_info, xs:string name, stringArray groups, xs:boolean asc, ), output: NgpObject

# This function sorts a dataset lexicographically by the names of row/column names (name) in ascending or descending order (asc); ascending by default.
# Additionally the user can apply the sorting of row/column labels in each groups (groups) from other attributes e.g. the other attributes: 'my_other_attr' has two groups: 'group1' and 'group2' with few elements in each group. Firstly the elements from each group will be sorted, and after that the names of groups will be sorted.
"""
try:
    grp = {"string": ["lps", "gcm", "mgcm"]}  #order
    sort_CR_result_obj = client.service.SortColumnsRows(dataset= data_obj, dataset_info= data_info, name= "treatment", groups= grp, asc= True )
    encoded_sort_CR_result = client.service.ReturnDataAsTSV(sort_CR_result_obj)
    print str(base64.b64decode(encoded_sort_CR_result[0]))
    print str(base64.b64decode(encoded_sort_CR_result[1]))
    print str(base64.b64decode(encoded_sort_CR_result[2]))
except:
    print 'SortColumnsRows() Failed. Details: %s' % sys.exc_info()[1]
"""
### 13. SortDataset(NgpObject dataset, DatasetInfo dataset_info, stringArray column_name, xs:boolean asc, ), output: NgpObject

#This function sorts a dataset by the values in the column(s) (column_name) in ascending or descending order (asc); ascending by default.
"""
col_name = {"string": ["GCH_A_Rat230_2.CEL", "GCH_B_Rat230_2.CEL"]} # NB: values in the column name ("file" in this example dataset)
try:
    sort_result_obj = client.service.SortDataset(dataset= data_obj, dataset_info= data_info, column_name= col_name, asc=True)
    encoded_sort_result = client.service.ReturnDataAsTSV(sort_result_obj)
    print str(base64.b64decode(encoded_sort_result[0]))
    print str(base64.b64decode(encoded_sort_result[1]))
    print str(base64.b64decode(encoded_sort_result[2]))
except:
    print 'SortDataset() Failed. Details: %s' % sys.exc_info()[1]
"""
### 14. TakeByColumnRow(NgpObject dataset, OtherAttrArray selected_rows_columns, DatasetInfo dataset_info, ), output: NgpObject

# This function returns a subset of dataset. Specify the columns and/or rows names to extract in selected_rows_columns argument.
# The OtherAttr is part of NgpObject and contain following fields: attr__name - name of column/row attributes, attr__value - column/row value, and attr__type - 'row' or 'column'.

#### Tester's comment 1: input_col.attr__values is mentioned as input_col.attr__value in documentation. Missing "s".
"""
try:
    # here you can mention only the column specification and data from corresponding columns from all the rows will be retreived.
    input_col = client.factory.create("OtherAttr")
    input_col.attr__values = {"string": ["gcm","mgcm","lps"]} #{"string": ["C6"]}
    input_col.attr__name = "treatment" #"cell_type"
    input_col.attr__type = "column"

    input__list = {"OtherAttr": [input_col]}

    # the following part is used when you specify both columns and rows to be retreived.
    #input_row = client.factory.create("OtherAttr")
    #input_row.attr__type = "row"
    #input_row.attr__values = {"string": ["ENSRNOG00000014670", "ENSRNOG00000017383"]} #{"string": ["1433F_RAT", "1433B_RAT"]}

    #input__list = {"OtherAttr": [input_col,input_row]}
    take_result_obj = client.service.TakeByColumnRow(dataset= data_obj, selected_rows_columns= input__list, dataset_info= data_info)
    #with open("31_12_take_row_col_data_obj.txt", "w") as g:
    #    g.write(str(take_result_obj))
    #try:
    #    print getattr(take_result_obj.data_array)
    #except:
    #    print "could not get attr!!"
    encoded_take_result = client.service.ReturnDataAsTSV(take_result_obj)
    print str(base64.b64decode(encoded_take_result[0]))
except:
    print 'TakeByColumnRow() Failed. Details: %s' % sys.exc_info()[1]

#try:
#    fun_result_obj= client.service.DatasetFunPerRowCol(dataset= take_result_obj, function= ['mean'], per= "row")
#    #print fun_result_obj
#    encoded_fun_result = client.service.ReturnDataAsTSV(fun_result_obj)
#    #print str(base64.b64decode(encoded_fun_result[0]))
#except:
#    print 'DatasetFunPerRowCol() Failed. Details: %s' % sys.exc_info()[1]
"""

### Cluster Client
### 6. DoCluster(NgpObject dataset, gap_stat, no_cluster), output: NgpObject
#This function computes k-means clustering. 

### Remove the Docstring quotes in the following section to invoke Cluster client!
# Start of Cluster_client_section #
"""
sys.stdout.write("\nMESSAGE: *** YOU HAVE INVOKED THE CLUSTER_CLIENT ***\n")
input_data_obj = data_obj
sys.stdout.write("\nMESSAGE: *** THE PROGRAM CAN CALCULATE THE NUMBER OF CLUSTERS FROM THE DATA. OR, YOU MAY MANUALLY PROVIDE THE NUMBER OF CLUSTERS YOU WANT. ***\n")
num_cluster_choice = rlinput("\nDo You Want to Provide the Number of Clusters Manually?[options: yes/no]: ", "no")
num_cluster_choice = num_cluster_choice.lower()
num_cluster_choice_set = ["yes", "no"]
if num_cluster_choice in num_cluster_choice_set:
    if num_cluster_choice == "no":
        num_cluster = False
    else:
        user_num_clust = int(rlinput("\nPlease Provide the Number of Clusters Manually[example: 5]: "))
        num_cluster = user_num_clust #int(user_num_clust)
else:
    print "You have provided illegal value!! You are funny!"

stat_score_choice = rlinput("\nBetween Gap-score and Silhouette-Score, Which Statistic Do You Want to Use?[options: gap/sil]: ", "gap")
stat_score_choice = stat_score_choice.lower()
if stat_score_choice == "gap":
    gap_stat_chosen = True
else:
    gap_stat_chosen = False
try:
    if num_cluster == False:
        cluster_obj = client.service.DoCluster(input_data_obj, gap_stat= gap_stat_chosen)
    else:
        cluster_obj = client.service.DoCluster(input_data_obj, gap_stat= gap_stat_chosen, no_cluster= num_cluster)

    # for writing data to file, uncomment the following lines:
    encoded_file_clust = client.service.ReturnDataAsTSV(cluster_obj)
    sys.stdout.write("\nMESSAGE: *** PLEASE FIND THE RESULTS IN THE FOLLOWING FILE IN THE PRESENT DIRECTORY: cluster_output_%s.txt ***\n"%(data_name))
    time = datetime.datetime.now()
    with open("cluster_output_%s.txt"%(data_name), "w")as f_clust:
        file_intro_clust = "### Result of clustering performed on %s dataset.\n### %s\n"%(data_name,time)
        f_clust.write(file_intro_clust)
        f_clust.write(str(base64.b64decode(encoded_file_clust[0])))
except:
    print 'Cluster Failed. Details: %s' % sys.exc_info()[1]
"""
# End of Cluster_client_section #
