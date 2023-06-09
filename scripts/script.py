from core.models import  *
import csv


def run():
    with open('objects.xls') as file:
        reader = csv.reader(file)
        next(reader)  # Advance past the header

        Item.objects.all().delete()

        for row in reader:
            print(row)
            category, _ = Category.objects.get_or_create(subcategory=SubCategory.objects.get_or_create(title=row[1]))
            item = Item(title=row[3],
                        articul=row[4],
                        category=category,
                        price=int(row[7]),
                        description="Норма упаковки:" + row[6]
                    )
            item.save()