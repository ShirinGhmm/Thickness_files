import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math
import os
from statistics import mean 
class thickness_file:
    keywords = ["Thickness","thickness", "nm", "Thickness (nm)", "Thickness(nm)", "thickness (nm)", "Schichtdicke nm","Film thickness [nm]"]
    avg_keywords= ['Avg.', 'Avg:', 'Average', 'Avg. Thickness','Average Thickness']
    ma_keywords = ['Cross Nr.']
    time_keywords=['Time', 'time', 'Time:']
    power_keywords = ['Power', 'Power:']
    rate_keywords = ['Rate','rate','Rate:','Rate/Power:']
    power_supply_keywords = ['DC', 'RF', 'DCp', 'dc,', 'Rf']
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_extention = os.path.splitext(file_path)[1]
        self.encoding_read_file = "ISO-8859-1"
        
    def find_type_and_keyword(self):
       
        file_extention = self.file_extention
        file_path = self.file_path
        
        count_col_no = 0
        count_l = 0
        float_list =[]
        same_col_dict = {}
        count_keyword = 0 
        count_fl =0
        count_str= 0
        stop_point = 0
        non_meas = 0
        column_index = []
        
        if file_extention == '.txt' or file_extention == '.dat':
        ### When the extention is .txt or .dat we investigate the file row by row and count the floats in each row
        ### by considering the index of float in the row list we will see how many floats can be in each column!
            with open(file_path, 'r',encoding = self.encoding_read_file) as f:
                for line in f:
                    count_l += 1
                    for word in thickness_file.keywords:
                        if word in line: 
                            count_keyword +=1
                    if (',') in line:
                        row = line.split(',')
                    else:
                        row = line.split()
                    #print(row)
                    col_no = len(row)
                    if col_no>0:
                        for r in row:
                            #r = r.replace(',','  ')
                            #print(r)
                            try:
                                float(r)
                                count_fl +=1
                                column_index.append(row.index(r))
                            except ValueError:
                                count_str +=1
            float_list.append(count_fl)
            
            same_col_dict["keyword"] = count_keyword
            ### in the following it can be found out there is a column with more that 2 float values.
            ### This is the criteria of validation.
            for i in column_index:
                if column_index.count(i)> 0:
                    same_col_dict["measurement_count"] = column_index.count(i)
                    break
                      
        if file_extention == '.xlsx':
        ### When the extention is .xlsx we investigate the file column by column and count the floats in each column
            df = pd.read_excel(file_path)
        ### opening .xlsx file by pandas returns empty values by NaN that is not known by fastAPI
        ### to avoid this using following line NaN will be converted to None that is known by python and fastAPI
            df = df.where(pd.notnull(df), None)
            for i in range(len(df.columns)):
                count_fl = 0
                col = df.iloc[:,i].tolist()
                for c in col:
                    if c != None:
                        try:
                            float(c)
                        ## because nan is count as float after reading .xlsx by pandas only the float > 0 are considered
                            count_fl +=1
                        except ValueError:
                            count_str +=1
            ### with the following condition if the number of floats values in a column is at least two, it will be saved in float_list
                if count_fl > 1:float_list.append(count_fl)
             
            ### here the file will be investigated row by row to find keyword
            for word in thickness_file.keywords:
                if word in df.columns:
                    count_keyword +=1
                for j in range(len(df.index)):
                    list_rows= list(df.iloc[j][0:len(df.columns)])
                    if word in list_rows:
                        count_keyword +=1
             
            same_col_dict["keyword"] = count_keyword
            
        ### for measurement count in .xlsx files the column with the highest number of float numbers is considered
            if len(float_list)> 0:
                same_col_dict["measurement_count"] = max(float_list)

        return same_col_dict
    
    def validity_check(self):
        same_col_dict= self.find_type_and_keyword()
        ma, thickness_list = self.find_thickness_ma()
        if len(same_col_dict) < 2:
            return {"Code":500,
                    "Message":"This file is not valid:Table of measurement not found",
                    "Warning":None}

        if len(same_col_dict)>1 and same_col_dict["keyword"] == 0:
            return {"Code":500,
                   "Message":"Table of measurement was found but a keyword related to thickness was not found",
                   "Warning":None}
        
        if len(same_col_dict)>1 and same_col_dict["keyword"] > 0 and len(thickness_list) <= 0:
            return {"Code":500,
                   "Message":"Table of measurement was found but the values of thickness not found",
                   "Warning":None}
        
        if len(same_col_dict)>1 and same_col_dict["keyword"] > 0 and len(thickness_list) > 0 :
            return {"Code":0,
		            "Message":None,
                    "Warning":None}

    def find_dataFrame(self):
        same_col_dict= self.find_type_and_keyword()
        if len(same_col_dict) < 2:
            raise ValueError('Table of measurement not found')
        if len(same_col_dict)>1 and same_col_dict["keyword"] == 0:
            raise ValueError("Table of measurement was found but a keyword related to thickness was not found")
        
        file_path = self.file_path
       
        count = 0
        tries = 0
        found_keyword = ''
        col_name = ''
        list_rows=[]
        skiprows = []
        dict_rows = {}
        count_l = 0
        index_w=0
        col_pos = 100
        count_f = 0
        count_s = 0
        count_f_before = 0
        count_f_after = 0
        count_s_before = 0
        count_s_after = 0
        vr =0
        df = {}
        if self.file_extention == '.txt':
            with open(self.file_path, 'r',encoding = "ISO-8859-1") as f:
                for line in f:
                    count_l+= 1
                    row = line.split()
                    dict_rows[count_l] = row       
            df = pd.DataFrame.from_dict(dict_rows, orient='index')
            df = df.where(pd.notnull(df), None)
            columns_names = df.columns
            #print(df)
           #print(df.columns)
        
            for i in range(len(df.index)):
                list_rows= list(df.iloc[i][0:len(columns_names)])
                
                for word in thickness_file.keywords:
                    
                    if word in columns_names:
                        found_keyword += word
                        index_w = columns_names.index(word)
                        skiprows = None
                        count += 1
                        break
                       
                    elif word in list_rows:
                        found_keyword += word
                        index_w = list_rows.index(word)
                        col_pos = index_w
                        column_name = columns_names[col_pos]
#                         print(col_pos)
#                         print(column_name)
                        j = list(df[column_name])[i+1]
                        print(j)
                        if j != None:
                            try:
                                float(j)
                                if math.isnan(float(j)) == False:
                                    count_f += 1

                            except ValueError:
                                count_s +=1
                            
                        print(count_f)
                        if count_f== 0 and list_rows[index_w-1] != None:
                            try:
                                float(list_rows[index_w-1])
                                if math.isnan(float(list_rows[index_w-1])) == False:
                                    count_f_before +=1

                            except ValueError:
                                count_s_before +=1
                                
                        if count_f == 0 and count_f_before==0 and index_w+2 in range(len(list_rows)+1): 
                            try:
                                x= list_rows[index_w+1] 
                                if x != None:
                                    try:
                                        float(list_rows[index_w+1])
                                        if math.isnan(float(list_rows[index_w+1])) == False:
                                            count_f_after +=1
                                    except ValueError:
                                        count_s_after +=1
                            except ValueError:
                                vr += 1
                   # print(count_f, count_f_before, count_f_after)
                    if count_f!= 0 or count_f_before != 0 or count_f_after != 0:

                        skiprows = range(0,i+1)
                        count += 1
                        break
                    else: continue
                
                if count > 0:                     
                    break
                else:
                    continue
            
            #print(count_f_before, count_f_after)
            print(skiprows)
            if count_f_before == 1 or count_f_after == 1:
                skiprows= skiprows[:-1]
                
            if count_f_before == 0 and count_f_after == 1:
                col_pos +=1
            elif count_f_before == 1:
                col_pos -= 1
            
            #print(col_pos)

            t = len(skiprows)
            df_new = pd.DataFrame.from_dict(dict(list(dict_rows.items())[t:]), orient='index')
            df_new = df_new.where(pd.notnull(df_new), None)
#             print(df_new.columns[0])
#             print(range(len(df_new.columns)))
            if col_pos != 100:
                if col_pos in range(len(df_new.columns)):
                    col_name = df_new.columns[col_pos]
                    df_new = df_new.rename(columns={col_name:'Thickness(nm)'})
                elif col_pos not in range(len(df_new.columns)) and len(df_new.columns)==1:
                    col_name = df_new.columns[0]
                    df_new = df_new.rename(columns={col_name:'Thickness(nm)'})
                    
        
        if self.file_extention == '.xlsx':
            df = pd.read_excel(file_path)
            df = df.where(pd.notnull(df), None)
            for i in range(len(df.index)):
                list_rows= list(df.iloc[i][0:len(df.columns)])
                for word in thickness_file.keywords:
                    if word in df.columns:
                        found_keyword += word
                        skiprows = None
                        count += 1
                        break
   
                    elif word in list_rows:
                        found_keyword += word
                        index_w = list_rows.index(word)
                        col_pos = index_w
                        if list_rows[index_w-1] != None:
                            try:
                                float(list_rows[index_w-1])
                                if math.isnan(float(list_rows[index_w-1]))==False: 
                                    count_f_before +=1
                            except ValueError:
                                count_s_before +=1
                        if index_w+2 in range(len(list_rows)+1): 
                            try:
                                x= list_rows[index_w+1] 
                                if x != None:
                                    try:
                                        float(list_rows[index_w+1])
                                        if math.isnan(float(list_rows[index_w+1]))==False: 
                                            count_f_after +=1
                                    except ValueError:
                                        count_s_after +=1
                            except ValueError:
                                vr +=1
                        skiprows = range(0,i+1)
                        count += 1
                        break
                    else:
                        tries +=1
                if count > 0:                     
                    break
                else:
                    continue
          
            if count_f_before == 1 or count_f_after == 1:
                skiprows= skiprows[:-1]
            
            if count_f_before == 0 and count_f_after == 1:
                col_pos +=1
            elif count_f_before == 1:
                col_pos -= 1

            df_new = pd.read_excel(file_path, skiprows= skiprows)
            df_new = df_new.where(pd.notnull(df_new), None)
            if col_pos != 100:
                if col_pos in range(len(df_new.columns)):
                    col_name = df_new.columns[col_pos]
                    df_new = df_new.rename(columns={col_name:'Thickness(nm)'})
                elif col_pos not in range(len(df_new.columns)) and len(df_new.columns)==1:
                    col_name = df_new.columns[0]
                    df_new = df_new.rename(columns={col_name:'Thickness(nm)'})
        

        return df, skiprows, found_keyword, df_new
    
    def table_of_df(self):
        """
            In this function a dataframe generated by find_dataFrame() will be read row by row 
            then the value of each cell of a row will be associated to its corresponding column name in a dictionary. 
            Therefor each row will have a dictionary. 
            All the dictionaries will be appended to a list (data_table). at the the jason file of DataTable will be returned. 
        """
        df, skiprows, found_keyword, df_new = self.find_dataFrame()
        
        row_list = []
        data_table = []
        df_row_dict = {}
        cols = list(df.columns)
    
        for i in range(len(df)):
            for j,c in enumerate(cols):
                celll = list(df.iloc[i])[j] 

                ##### any method to take a cell value from a dataframe will return the value as numpy.float64 or numpy.int64 
                ##### numpy values cannot be used in dictionary in fastAPI , so I used item() method to just have normal int and float :<<<
                
                if type(celll) == np.float64 or type(celll) == np.int64 :
                    cell_val = celll.item()
                else:
                    cell_val = celll
                    
                #print(type(cell_val))
                #The below method for taking cell value didnt work for txt files but it is easier than iloc!
                #cell_val = df.at[i, c].item()
                
                df_row_dict[c] = cell_val
            data_table.append(df_row_dict)
            df_row_dict = {}
#               
        
        return {
                "DataTable":data_table
                }      
        
### if df.column has keyword the value under it will be considered othewise the column with values should be found !!!  
    def find_thickness_ma(self):
        df, skiprows, found_keyword, df_new = self.find_dataFrame()
        thickness_vals_init = []
        thickness_vals = []
        columns_name = list(df_new.columns)
        thkl = []
        float_columns = []
        stop_point = 0
        non_f = 0
        ma = []
        list_common_para= list(set(columns_name) & set(thickness_file.keywords))
        #print(list_common_para)
        for i in range(len(df_new.index)):
            list_rows = list(df_new.iloc[i][0:len(df_new.columns)])
            for j in thickness_file.avg_keywords:
                if j in list_rows:
                    stop_point = i
                    break
            if stop_point > 0:
                break
        
        sp = -(len(df_new.index)-stop_point)
        if len(list_common_para) > 0:
            common_para = list_common_para[0]
            if stop_point != 0:
                thickness_vals_init= list(df_new[common_para])[:sp]
                for word in thickness_file.ma_keywords:
                    if word in list(set(columns_name)):
                        ma= list(df_new[word])[:sp]
            else:
                thickness_vals_init= list(df_new[common_para])
                for word in thickness_file.ma_keywords:
                    if word in list(set(columns_name)):
                        ma= list(df_new[word])

            for t in thickness_vals_init:
                if t != None:
                    try:
                        float(t)
                        if math.isnan(float(t))==False:
                            thickness_vals.append(float(t))
                    except ValueError:
                        non_f += 1
       
            
        return ma, thickness_vals
                 
       
            
        
    
    def find_power_time_rate(self):
        df, skiprows, found_keyword, df_new = self.find_dataFrame()
        list_row= [list(df.columns)]
        time = 0
        power = 0
        rate_list1 = []
        rate_list = []
        power_supply = ''
        rate = 0
        rate_per_power = 0
        count_str = 0
        for i in range(len(df.index)):
                list_row.append(list(df.iloc[i][0:len(df.columns)]))
        #print(list_row)       
        for j in list_row:
            for k in j:
                index_k = j.index(k)
                if type(k)== str:
                    for word in thickness_file.time_keywords:
                        if word in k.split():
                            if index_k+1 in range(len(j)):
                                if j[index_k+1]!= None and j[index_k+1]!= '=':
                                    time = j[index_k+1]
                                elif index_k+2 in range(len(j)):
                                    if j[index_k+2] != None:
                                        time = j[index_k+2]
                                else:
                                    time= None
                            break
                    for word in thickness_file.power_keywords:        
                        if word in k.split():
                            if index_k+1 in range(len(j)):
                                if j[index_k+1]!= None and j[index_k+1]!= '=':
                                    power = j[index_k+1] 
                                elif index_k+2 in range(len(j)):
                                    if j[index_k+2]!= None:
                                        power = j[index_k+2]
                                else:
                                    power = None
                            break
                    for word in thickness_file.rate_keywords:        
                        if word in k.split():
                            if index_k+1 in range(len(j)):
                                print(j[index_k+1])
                                if j[index_k+1] != None and j[index_k+1] != '=':
                                    rate_list1.append(j[index_k+1])
                                elif index_k+2 in range(len(j)):
                                    print(j[index_k+2])
                                    if j[index_k+2] != None:
                                        rate_list1.append(j[index_k+2])                            
                                    
                            break
                    for word in thickness_file.power_supply_keywords:
                        if word in k.split():
                            power_supply = word
                            break
                    
        #### Checking if the obtained values for time, power and rate from data file are floatable or not
        #### If the values are not floatable, they can not be accepted 
        
        if time == 0:
            time = None 
        else:
            try:
                float(time)
                time = float(time)
            except ValueError:
                time = None
        print(time)
        if power == 0:
            power = None 
        else:
            try:
                float(power)
                power = float(power)
            except ValueError:
                power = None   
            
        for f in rate_list1:
            try:
                float(f)
                rate_list.append(float(f))
            except ValueError:
                count_str += 1
                
        if power_supply == '':
            power_supply= None
                    
        #rate_list = [x for x in rate_list if type(x) != str]
        #print(rate_list)
            
        if len(rate_list) == 0:
            rate = None
            rate_per_power = None
        if len(rate_list) == 1:
            rate = rate_list[0]
            rate_per_power = None
        if len(rate_list) == 2:
            rate = max(rate_list)
            rate_per_power = min(rate_list)
            if min(rate_list) == max(rate_list):
                   rate_per_power= None
       
                 
        return time, power, rate, rate_per_power, power_supply
                

    def thickness_ma_for_database(self):
        ma_val, thickness_vals = self.find_thickness_ma()
        time, power, rate, rate_per_power, power_supply = self.find_power_time_rate()
        properties_MA_thickness = []
        properties_overall_thickness = []
        thickness_vals= [x for x in thickness_vals if x !=0 and x!=None]
        if len(thickness_vals) == 0:
            raise ValueError ('The list of Thickness values has no float numbers')
        
    
        if len(ma_val)== 0:
            thickness = mean(thickness_vals)
            thickness_min = min(thickness_vals)
            thickness_max = max(thickness_vals)
            ma = 168
            properties_MA_thickness.append({"Predicate": {
                                            "Properties": [
                                                {
                                                  "Type": 2,
                                                  "Name": "Measurement Area",
                                                  "Value": ma
                                                }
                                              ]
                                            },
                                            "DeletePreviousProperties": False,
                                            "Properties": [
                                              {
                                                "PropertyId": 0,
                                                "Type": 1,
                                                "Name": "Thickness",
                                                "Value": thickness,
                                                "ValueEpsilon": None,
                                                "SortCode": 10,
                                                "Row": None,
                                                "Comment": "Average Thickness in nm at center of MAs"
                                              },
                                              
                                            ]})
            properties_overall_thickness.append(
                                                {
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "Thickness",
                                                  "Value": thickness_min,
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": 1,
                                                  "Comment": "Minimal Thickness in nm of Materials Library at center of MAs"
                                                })
            properties_overall_thickness.append({
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "Thickness",
                                                  "Value": thickness_max,
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": 2,
                                                  "Comment": "Maximal Thickness in nm of Materials Library at center of MAs"
                                                })
            properties_overall_thickness.append({
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "MeasurementsCount",
                                                  "Value": len(thickness_vals),
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": None,
                                                  "Comment": "Thickness Measurements Count of Materials Library at center of MAs"
                                                })
            
            
            
        if len(ma_val) > 0:
            count = 0
            thickness = mean(thickness_vals)
            thickness_min = min(thickness_vals)
            thickness_max = max(thickness_vals)
            for i in thickness_vals:
                index_i = thickness_vals.index(i)
                thickness = i
                ma = ma_val[index_i]
                
                properties_MA_thickness.append({"Predicate": {
                                            "Properties": [
                                                {
                                                  "Type": 2,
                                                  "Name": "Measurement Area",
                                                  "Value": ma
                                                }
                                              ]
                                            },
                                            "DeletePreviousProperties": False,
                                            "Properties": [
                                              {
                                                "PropertyId": 0,
                                                "Type": 1,
                                                "Name": "Thickness",
                                                "Value": thickness,
                                                "ValueEpsilon": None,
                                                "SortCode": 10,
                                                "Row": None,
                                                "Comment": f"Average Thickness in nm at MA= {ma}"
                                              },
                                              
                                            ]})
            properties_overall_thickness.append(
                                                {
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "Thickness",
                                                  "Value": thickness_min,
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": 1,
                                                  "Comment": "Minimal Thickness in nm of Materials Library (of all 342 MAs)"
                                                })
            properties_overall_thickness.append({
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "Thickness",
                                                  "Value": thickness_max,
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": 2,
                                                  "Comment": "Maximal Thickness in nm of Materials Library (of all 342 MAs)"
                                                })
            properties_overall_thickness.append({
                                                  "PropertyId": 0,
                                                  "Type": 1,
                                                  "Name": "MeasurementsCount",
                                                  "Value": len(thickness_vals),
                                                  "ValueEpsilon": None,
                                                  "SortCode": 10,
                                                  "Row": None,
                                                  "Comment": "Thickness Measurements Count of Materials Library (of all 342 MAs)"
                                                })
            
                        
        return {
                  "CompositionsForSampleUpdate":properties_MA_thickness,
                  "DeletePreviousProperties": True,
                  "Properties": properties_overall_thickness
                }
                
                                  