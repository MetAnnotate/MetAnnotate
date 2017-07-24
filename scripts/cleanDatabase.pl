unless (@ARGV)
{	print "Cleans a protein multi-fasta file to remove non-standard amino acids\n";
	print "usage perl $0 <input file (fasta)>\n";
}

open FILE,$ARGV[0];

@toRemove = ();

while (<FILE>)
{

	if (substr($_,0,1) eq ">")
	{	substr($_,0,1) = "";
		$fn = $_;
	}
	else
	{	if ($_ =~ /[uUoOjJzZxXbB]/g)
		{	push (@toRemove,$fn);
		}
	}
}

close FILE;

foreach (@toRemove)
{	print;
	#print "\n";
}
