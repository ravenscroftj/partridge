import glob
import os
import click

@click.command()
@click.argument("train_dir", type=click.Path(dir_okay=True, exists=True))
def main(train_dir):
    
    types = os.listdir(train_dir)

    for type in types:
        papercount = len(glob.glob(os.path.join(train_dir, type, "*_annotated.xml")))

        print(type, papercount)

if __name__ == "__main__":
    main()