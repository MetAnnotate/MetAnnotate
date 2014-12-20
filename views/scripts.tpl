% rebase('base.tpl', js='default')

<p>
MetAnnotate output files can be further analyzed offline using some of the following R scripts.
<p>

<h3>Loading and processing output files</h3>
<br>

Set your working directory. For example, this may be the directory containing the .tsv MetAnnotate results file. E.g.,

<pre>
setwd("~/Desktop/MetAnnotateResults/")
</pre>

Load your dataset (here, it is a tab-separated file called data.tsv):

<pre>
tb <- read.delim("data.tsv",sep='\t',header=T)
</pre>

You may now want to look at the counts (# hits for all HMMs) for each dataset

<pre>
sort(table(tb[,1]))
</pre>

If there are datasets with very few (e.g., 50 or less) counts, you may want to remove them:
<pre>
print("Removing...")
which(table(tb[,1]) < 50)

for (d in names(which(table(tb[,1]) < 50)))
{
	tb <- tb[-which(tb[,1] == d),]
}
</pre>

<h3>Plotting</h3>

<h4>Barplots</h4>

The first thing you need to decide on is the data column you want to analyze.
For <strong>order</strong> level taxon assignments predicted using the <strong>tree-based method</strong> ...

<pre>
k <- "Representative.Order" # can be Species, Genus, Family, Order, Class...
</pre>

Now run the following code to make your barplot

<pre>

# a color scheme
pal12 = c("#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99", 
"#E31A1C", "#FDBF6F", "#FF7F00", "#CAB2D6", "#6A3D9A", 
"#FFFF99", "#B15928") 
cols <- colorRampPalette(pal12)(length(levels(as.factor(tb[,k]))))

par(mfrow=c(1,2))

tb.2 <- t(table(tb[,c(1,which(colnames(tb) == k))]))
for (i in 1:ncol(tb.2))
{
	tb.2[,i] <- tb.2[,i] / sum(tb.2[,i])
}

tb.2 <- t(na.omit(t(tb.2)))


## suppose you want to reorder the barplot and show only a subset of datasets in a specific order. Uncomment the following two lines
# datasetOrder <- c("4446153","4477804","4537195","SRR908273a")  # a hypothetical list of datasets
# tb.2 <- tb.2[,match(datasetOrder,colnames(tb.2))]

barplot(tb.2,col=cols,las=3, cex.names=0.5)
plot.new()

legend("left", inset=.05, title="Class",legend =
  	c(levels(as.factor(tb[,k]))), fill = cols,cex=0.2)

</pre>

<h4>Clustered Heatmap</h4>

You will need to have the pheatmap package installed.

<pre>
library(pheatmap)
</pre>

As before, you need to pick a taxonomic level. This time it is called sColumn

<pre>
sColumn <- "Representative.Genus" #species column for which to do the species breakdown/analysis
</pre>

Since showing all taxa may be overwhelming, we can choose to show only the most frequent species -- those present greater than some threshold in at least one dataset. This is done with the mpt parameter

<pre>
mpt <- 0.02 #max fraction of a taxa in any dataset required for inclusion in heat map
</pre>

The following parameter can also be set to less to reduce the size of labels in the heatmap

<pre>
cexVal <- 1
</pre>

Now run...

<pre>

matr <- table(tb[,k],tb[,1])
matr <- sweep(matr, 2, colSums(matr), "/")
maxPerTaxa <- apply(matr,1,max)
cexVal <- 1 #sets size of labels
ll <- pheatmap((matr[which(maxPerTaxa > mpt),]),cex=cexVal)

</pre>

<h3>Principal coordinates analysis (PCOA)</h4>

PCOA is really easy in R. First load the vegan package

<pre>
library(vegan)
</pre>

Just run:

<pre>
D <- vegdist(t(matr[which(maxPerTaxa > mpt),]))   ## works better when rare species are removed
biplot(pcoa(D))
</pre>


