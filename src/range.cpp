#include "unc_ctype.h"
#include "range.h"


// similar to https://linux.die.net/man/1/filterdiff
bool parse_range(const char *str, std::vector<range_t> &ranges)
{
   bool was_dash = false;
   unsigned long line = 1;
   unsigned long prev_line = 1;

   if (str == NULL)
   {
      return false;
   }

   while (*str != 0)
   {
      if (unc_isspace(*str))
      {
         str++;
         continue;
      }

      if (unc_isdigit(*str))
      {
         char *ptmp;
         line = strtoul(str, &ptmp, 10);
         str = ptmp;

         if (was_dash)
         {
            was_dash = false;
         }
         else
         {
            prev_line = line;
         }
      }
      else if (*str == '-')
      {
         was_dash = true;
         str++;
      }
      else  /* probably a comma */
      {
         // avoid unsigned overflow
         if (prev_line > line)
         {
            return false;
         }
         range_t r = { prev_line, line - prev_line };
         ranges.push_back(r);
         line = 0;
         prev_line = 0;
         was_dash = false;
         str++;
      }
   }

   if (line != 0 && prev_line != 0)
   {
      range_t r = { prev_line, was_dash ? -1 : line - prev_line };
      ranges.push_back(r);
   }

   return true;
}
