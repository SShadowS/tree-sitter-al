# Remaining Keywords to Convert to RustRegex

## Summary
Found numerous keywords still using explicit case choices instead of case-insensitive RustRegex patterns.

## Keywords to Convert:

### Object Declaration Keywords
- namespace
- xmlport  
- enum
- enumextension
- query
- pageextension
- tableextension
- table
- page
- report
- codeunit (already done)
- interface
- controladdin
- permissionset
- permissionsetextension
- profile
- pagecustomization
- entitlement
- dotnet

### Property Keywords
- implements
- extends
- value
- sourcetableview
- sourcetable
- enabled
- visible
- subtype (has extra case "Subtype")
- drilldownpageid
- lookuppageid
- caption
- captionml
- description
- tooltip (already done)
- tooltipml
- datacaptionfields
- optionmembers
- optioncaption
- optioncaptionml
- tablerelation
- calcformula
- editable
- fieldclass
- initvalue
- access
- assignable
- datapercompany
- moveonactivate
- savevalues
- lookupmode
- popuplateallfields
- instructionaltext
- instructionaltextml
- showmandatory
- showfilter
- multiplelines
- closeonescape
- linkedobject
- linkedintable
- previewmode
- homeitemspage
- actionspage
- customizationspage

### Field and Type Keywords  
- field
- fields
- key
- keys
- fieldgroup
- fieldgroups
- code
- text
- integer
- decimal
- boolean
- date
- time
- datetime
- option
- blob
- guid
- recordid (already done)
- variant
- char
- byte
- duration
- dateformula
- biginteger
- media
- mediaset
- textbuilder

### Trigger Keywords
- trigger
- onrun
- oninsert
- onmodify
- ondelete
- onrename
- onvalidate
- onlookup
- onaftergetrecord
- oninit
- onopenpage
- onclosepage
- onnewrecord
- oninsertrecord
- onmodifyrecord
- ondeleterecord
- onqueryclosepage
- onaftergetcurrrecord

### Statement Keywords
- begin
- end
- if
- then
- else
- case
- of
- for
- to
- downto
- while
- repeat
- until
- exit
- break
- with
- do

### Operator Keywords
- and
- or
- not
- xor
- div
- mod
- in

### System Keywords
- system
- database
- const
- filter
- field
- lookup
- where
- count
- sum
- average
- min
- max
- exist

## Recommendation
Converting all these keywords to RustRegex would:
1. Make the grammar more consistent
2. Handle all case variations automatically
3. Reduce grammar size
4. Simplify maintenance

However, this is a large change that should be done carefully and tested thoroughly.