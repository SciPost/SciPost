# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    # Create an immutable wrapper around unaccent
    # so that it can be used in generated fields.
    # We don't manually change the dictionary of the
    # transformation so it should be safe to mark as immutable.
    # Possible postgres updates may break the index, but
    # we can recreate it if needed.
    #
    # SQL from: https://neon.com/docs/extensions/unaccent
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text
            AS $$
              SELECT public.unaccent('public.unaccent', $1);
            $$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT;
            """,
            reverse_sql="""
            DROP FUNCTION IF EXISTS immutable_unaccent(text);
            """,
        )
    ]
