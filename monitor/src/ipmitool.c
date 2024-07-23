/* Created by Kristen Guernsey (kguerns), July 2024
   Captures instantaneous power reading from ipmitool (Baseboard Management Controller)
   */

#include <stdio.h>
#include <stdlib.h>
#include "stats.h"


#define KEYS \
    X(power, "U=W", "instantaneous power")


static void ipmitool_collect(struct stats_type *type)
{
    FILE *file = NULL;
    char buf[80];
    unsigned int power;

    /* Open ipmitool command for reading. Output formatted to only get the number. */
    file = popen("/bin/ipmitool dcmi power reading | grep Instantaneous | awk \'{print $(NF-1)}\'", "r");
    if (file == NULL) {
        printf("Failed to run ipmitool command\n" );
        goto out;
    }

    /* Store command output */
    if (fgets(buf, sizeof(buf), file) != NULL) {
        printf("Power (W) = %s\n", buf);    // Testing; remove later
	    power = atoi(buf);
    } else {
        goto out;
    }

    pclose(file);
    file = NULL;

    struct stats *stats = NULL;
    stats = get_current_stats(type, NULL);
    if (stats == NULL)
        goto out;

    power = 2;  // Testing; remove later
    stats_set(stats, "power", power);

    out:
        if (file != NULL)
            pclose(file);
        file = NULL;
}

struct stats_type ipmitool_stats_type = {
    .st_name = "ipmitool",
    .st_collect = &ipmitool_collect,
#define X SCHEMA_DEF
    .st_schema_def = JOIN(KEYS),
#undef X
};
