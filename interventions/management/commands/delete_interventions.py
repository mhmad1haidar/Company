from django.core.management.base import BaseCommand
from interventions.models import Intervention


class Command(BaseCommand):
    help = 'Delete all intervention data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )

    def handle(self, *args, **options):
        count = Intervention.objects.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No interventions found to delete.'))
            return

        if not options['confirm']:
            confirm = input(f'Are you sure you want to delete {count} intervention(s)? Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Deletion cancelled.'))
                return

        # Delete all interventions
        deleted_count, _ = Intervention.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} intervention(s).')
        )
