---
title: "SourceTableView Property (XMLports)"
ms.date: 04/01/2021
ms.topic: reference
ms.assetid: f49d8c45-f2e6-4c96-a53b-31ddd1883e3b
caps.latest.revision: 4
author: SusanneWindfeldPedersen
---

# SourceTableView Property (XMLports)
> **Version**: _Available from runtime version 1.0._

Sets the key, sort order, and filter of the source table presented to the user.
  
## Applies to  

- Table elements in XMLports  

## Syntax

```AL
SourceTableView = SORTING(Code);
```
 
## Remarks  

To sort a set of table fields in the table view, use the **sorting** keyword. To sort the records in ascending or descending order, use the **order** keyword.  And, to apply a set of filters in the table view, use the **where** keyword.

## See Also  

[Properties](devenv-properties.md)    // SourceTableView Property
    // Sets the key, sort order, and filter of the source table presented to the user.
    // This property is used on XMLport Table Elements.
    source_table_view_property: $ => seq(
      'SourceTableView',
      '=',
      field('value', $.string_literal),
      ';'
    ),
