## Code for turning a short fat matrix into long narrow
## and output as space delimited text 
## Author: S.Smart, Date: 01/09/2015

# 1. Data import. Read in matrix format with rows as species names and 
# columns as quadrat id's and entries as missings or a cover value as integer.

In<-read.csv("C:\\MAVIS\\Book1.csv")

# 2. Get number of columns in input matrix and define plot counter
maxcol<- ncol(In)
counter=1

# 3. Define a data frame to take the accumulated quadrat species lists plus covers
Out <- data.frame(x=integer(0), y=character(0), z=integer(0))
names(Out)[c(1,2,3)] <- c("Quadrat","Names","Cover")

# 4. Loop through matrix extracting each quadrat list and add to 'Out'
for (col in 2:maxcol)
{ 
    Quadrat <- na.omit(In[,c(1,col)])
    Qid<-rep(counter, times=nrow(Quadrat))
    Quadrat <-cbind(Qid,Quadrat) 
    names(Quadrat)[c(1,2,3)] <- c("Quadrat","Names","Cover")
    Out <- rbind(Out,Quadrat)
    counter=counter+1

}

# 5. Write to space delimited txt file
write.table(Out, "C:\\MAVIS\\Out.txt", 
col.names=FALSE, row.names=FALSE, quote=FALSE)

